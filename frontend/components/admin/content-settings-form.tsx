"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type ContentSettings = {
  banner_title: string;
  banner_description: string;
  logo_image_url: string;
  promo_title_l: string;
  promo_text_l: string;
  promo_title_c: string;
  promo_text_c: string;
  promo_title_r: string;
  promo_text_r: string;
};

type Props = {
  initial: ContentSettings;
};

function insertAround(textarea: HTMLTextAreaElement, before: string, after: string = "") {
  const start = textarea.selectionStart ?? 0;
  const end = textarea.selectionEnd ?? 0;
  const value = textarea.value;
  const selected = value.slice(start, end) || "text";
  const next = value.slice(0, start) + before + selected + after + value.slice(end);
  return next;
}

export function ContentSettingsForm({ initial }: Props) {
  const [values, setValues] = useState<ContentSettings>(initial);
  const [status, setStatus] = useState<string | null>(null);
  const textareaRefs: Record<string, HTMLTextAreaElement | null> = {};

  const set = (key: keyof ContentSettings) => (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValues((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const apply = (key: keyof ContentSettings, before: string, after: string = "") => {
    const textarea = textareaRefs[key];
    if (!textarea) return;
    const next = insertAround(textarea, before, after);
    setValues((prev) => ({ ...prev, [key]: next }));
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.setSelectionRange(textarea.selectionStart ?? 0, (textarea.selectionStart ?? 0) + next.length - values[key as string].length + (before.length + after.length));
    });
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus("Saving...");
    const data = new FormData();
    data.set("banner_title", values.banner_title);
    data.set("banner_description", values.banner_description);
    data.set("logo_image_url", values.logo_image_url);
    data.set("promo_title_l", values.promo_title_l);
    data.set("promo_title_c", values.promo_title_c);
    data.set("promo_title_r", values.promo_title_r);
    data.set("promo_text_l", values.promo_text_l);
    data.set("promo_text_c", values.promo_text_c);
    data.set("promo_text_r", values.promo_text_r);

    const response = await fetch("/api/admin/content", {
      method: "POST",
      body: data,
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      setStatus("Save failed.");
      return;
    }
    setStatus("Saved.");
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium">Banner title</label>
          <Textarea
            ref={(node) => { textareaRefs.banner_title = node; }}
            value={values.banner_title}
            onChange={set("banner_title")}
            className="mt-1"
            rows={2}
          />
          <div className="mt-2 flex gap-1">
            <Button type="button" variant="secondary" onClick={() => apply("banner_title", "**", "**")} className="text-xs">Bold</Button>
            <Button type="button" variant="secondary" onClick={() => apply("banner_title", "_", "_")} className="text-xs">Italic</Button>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium">Banner description</label>
          <Textarea
            ref={(node) => { textareaRefs.banner_description = node; }}
            value={values.banner_description}
            onChange={set("banner_description")}
            className="mt-1"
            rows={3}
          />
          <div className="mt-2 flex gap-1">
            <Button type="button" variant="secondary" onClick={() => apply("banner_description", "**", "**")} className="text-xs">Bold</Button>
            <Button type="button" variant="secondary" onClick={() => apply("banner_description", "_", "_")} className="text-xs">Italic</Button>
            <Button type="button" variant="secondary" onClick={() => apply("banner_description", "\n- ")} className="text-xs">Bullet</Button>
            <Button type="button" variant="secondary" onClick={() => apply("banner_description", "\n")} className="text-xs">Newline</Button>
          </div>
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium">Logo image URL</label>
          <input
            name="logo_image_url"
            value={values.logo_image_url}
            onChange={(event) => setValues((prev) => ({ ...prev, logo_image_url: event.target.value }))}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="https://example.com/logo.png"
          />
          <p className="mt-1 text-xs text-slate-600">Use an externally hosted image URL.</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {([
          ["promo_title_l", "promo_text_l", "Left title", "Left text"],
          ["promo_title_c", "promo_text_c", "Centre title", "Centre text"],
          ["promo_title_r", "promo_text_r", "Right title", "Right text"],
        ] as const).map(([titleKey, textKey, titleLabel, textLabel]) => (
          <div key={titleKey} className="space-y-2">
            <div>
              <label className="block text-sm font-medium">{titleLabel}</label>
              <Textarea
                ref={(node) => { textareaRefs[titleKey] = node; }}
                value={values[titleKey]}
                onChange={set(titleKey)}
                className="mt-1"
                rows={1}
              />
              <div className="mt-2 flex gap-1">
                <Button type="button" variant="secondary" onClick={() => apply(titleKey, "**", "**")} className="text-xs">Bold</Button>
                <Button type="button" variant="secondary" onClick={() => apply(titleKey, "_", "_")} className="text-xs">Italic</Button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium">{textLabel}</label>
              <Textarea
                ref={(node) => { textareaRefs[textKey] = node; }}
                value={values[textKey]}
                onChange={set(textKey)}
                className="mt-1"
                rows={3}
              />
              <div className="mt-2 flex gap-1">
                <Button type="button" variant="secondary" onClick={() => apply(textKey, "**", "**")} className="text-xs">Bold</Button>
                <Button type="button" variant="secondary" onClick={() => apply(textKey, "_", "_")} className="text-xs">Italic</Button>
                <Button type="button" variant="secondary" onClick={() => apply(textKey, "\n- ")} className="text-xs">Bullet</Button>
                <Button type="button" variant="secondary" onClick={() => apply(textKey, "\n")} className="text-xs">Newline</Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button type="submit" variant="secondary">Save homepage text</Button>
        {status ? <span className="text-xs text-slate-600">{status}</span> : null}
      </div>
    </form>
  );
}
