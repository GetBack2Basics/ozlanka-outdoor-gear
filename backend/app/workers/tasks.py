from datetime import datetime, timezone

from sqlalchemy import inspect, text, select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine, Base
from app.models import AppSetting, Product, ScrapeRun
from app.services.pricing import calculate_lkr_price
from app.services.scraper import build_pricing_payload, discover_product_targets, run_scrape
from app.services.exchange import get_aud_to_lkr_rate
from app.services.images import download_product_image
from app.workers.celery_app import celery


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("scrape_runs")}
    product_columns = {column["name"] for column in inspector.get_columns("products")}
    additions = {
        "stage": "ALTER TABLE scrape_runs ADD COLUMN stage VARCHAR(80) NOT NULL DEFAULT 'queued'",
        "progress_percent": "ALTER TABLE scrape_runs ADD COLUMN progress_percent INTEGER NOT NULL DEFAULT 0",
        "message": "ALTER TABLE scrape_runs ADD COLUMN message TEXT",
        "total_items": "ALTER TABLE scrape_runs ADD COLUMN total_items INTEGER NOT NULL DEFAULT 0",
        "processed_items": "ALTER TABLE scrape_runs ADD COLUMN processed_items INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        for column_name, ddl in additions.items():
            if column_name not in columns:
                connection.execute(text(ddl))
        if "source_lastmod_at" not in product_columns:
            connection.execute(text("ALTER TABLE products ADD COLUMN source_lastmod_at TIMESTAMPTZ"))


@celery.task(name="app.workers.tasks.trigger_scrape")
def trigger_scrape(run_id: int | str, source: str = "manual") -> dict[str, int | str]:
    ensure_schema()
    settings = get_settings()
    urls = [url.strip() for url in settings.scrape_target_urls.split(",") if url.strip()]
    db = SessionLocal()
    try:
        run_id_int = int(run_id)
    except (TypeError, ValueError):
        run_id_int = None
    run = db.get(ScrapeRun, run_id_int) if run_id_int is not None else None
    if run is None:
        run = db.execute(
            select(ScrapeRun)
            .where(ScrapeRun.source == source, ScrapeRun.status == "queued")
            .order_by(ScrapeRun.started_at.desc())
        ).scalars().first()
    if run is None:
        db.close()
        return {"run_id": 0, "count": 0, "status": "skipped"}
    run.source = source
    product_targets = discover_product_targets(urls)
    # Limit to 50 products max
    MAX_PRODUCTS = 50
    if len(product_targets) > MAX_PRODUCTS:
        product_targets = product_targets[:MAX_PRODUCTS]
    run.total_items = len(product_targets)
    run.processed_items = 0
    run.progress_percent = 0
    run.stage = "starting"
    run.status = "running"
    run.message = f"Discovered {len(product_targets)} product URLs"
    db.commit()
    if not product_targets:
        run.stage = "finished"
        run.status = "finished"
        run.progress_percent = 100
        run.message = "No product URLs found"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.close()
        return {"run_id": run.id, "count": 0, "status": "finished"}

    target_urls = [target.source_url for target in product_targets]
    target_lastmod = {target.source_url: target.lastmod for target in product_targets}
    existing_products = db.execute(select(Product).where(Product.source_url.in_(target_urls))).scalars().all()
    existing_by_url = {product.source_url: product for product in existing_products}

    scrape_urls: list[str] = []
    skipped_count = 0
    for target in product_targets:
        existing = existing_by_url.get(target.source_url)
        if (
            existing is not None
            and getattr(existing, "source_lastmod_at", None) is not None
            and target.lastmod is not None
            and existing.source_lastmod_at.date() == target.lastmod.date()
        ):
            skipped_count += 1
            continue
        scrape_urls.append(target.source_url)

    if skipped_count:
        _update_run_progress(
            db,
            run,
            skipped_count,
            run.total_items,
            "filtering-products",
            f"Skipped {skipped_count} unchanged products based on sitemap date",
        )
    try:
        scraped_products = run_scrape(
            scrape_urls,
            progress_callback=lambda processed, total, stage, message: _update_run_progress(
                db,
                run,
                skipped_count + processed,
                skipped_count + total,
                stage,
                message,
            ),
        )
        rate = get_aud_to_lkr_rate()
        handling_fee = settings.handling_fee_percent
        run.stage = "processing-products"
        run.message = "Processing scraped products"
        db.commit()
        processed_in_db = skipped_count
        for scraped in scraped_products:
            payload = build_pricing_payload(scraped, handling_fee)
            product = db.execute(select(Product).where(Product.source_url == scraped.source_url)).scalar_one_or_none()
            if product is None:
                product = Product(**payload, handling_fee_percent=handling_fee)
                db.add(product)
            else:
                for key, value in payload.items():
                    setattr(product, key, value)
                product.handling_fee_percent = handling_fee
            local_image = download_product_image(scraped.image_url, scraped.source_url)
            if local_image:
                product.image_url = local_image
            product.source_lastmod_at = target_lastmod.get(scraped.source_url)
            product.scraped_at = datetime.now(timezone.utc)
            processed_in_db += 1
            _update_run_progress(
                db,
                run,
                processed_in_db,
                run.total_items,
                "processing-products",
                f"Processed {processed_in_db} of {run.total_items} products",
            )
        setting = db.execute(select(AppSetting).where(AppSetting.key == "fx_rate_aud_lkr")).scalar_one_or_none()
        if setting is None:
            db.add(AppSetting(key="fx_rate_aud_lkr", value=str(rate)))
        else:
            setting.value = str(rate)
        run.stage = "finalizing"
        run.message = "Saving scrape results"
        run.status = "finished"
        run.progress_percent = 100
        run.processed_items = run.total_items
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"run_id": run.id, "count": len(scraped_products), "status": "finished"}
    except Exception as exc:
        run.status = "failed"
        run.stage = "failed"
        run.message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise exc
    finally:
        db.close()


def _update_run_progress(db: SessionLocal, run: ScrapeRun, processed_items: int, total_items: int, stage: str, message: str) -> None:
    run.processed_items = processed_items
    run.total_items = total_items
    run.stage = stage
    run.message = message
    if total_items > 0:
        run.progress_percent = min(99, int((processed_items / total_items) * 100))
    else:
        run.progress_percent = 0
    db.commit()
