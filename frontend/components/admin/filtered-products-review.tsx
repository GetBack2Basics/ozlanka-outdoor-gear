"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";


type FilteredProduct = {
  id: number;
  name: string;
  source_url: string;
  image_url: string | null;
  price_aud: number;
  price_lkr: number;
  sku: string | null;
  description: string | null;
  category: string | null;
  is_bundle: boolean;
  filter_reason: string;
};

interface FilteredProductsReviewProps {
  initialProducts?: FilteredProduct[];
  token?: string;
}

export function FilteredProductsReview({ initialProducts = [], token }: FilteredProductsReviewProps) {
  const [filteredProducts, setFilteredProducts] = useState<FilteredProduct[]>(initialProducts);
  const [loading, setLoading] = useState(!initialProducts.length);
  const [actionLoading, setActionLoading] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [reasonFilter, setReasonFilter] = useState("all");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  const fetchFilteredProducts = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const response = await fetch("/api/admin/products/filtered", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setFilteredProducts(data);
        setSelectedIds(new Set());
        setSelectAll(false);
      }
    } catch (error) {
      console.error("Failed to fetch filtered products:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (loading && !initialProducts.length) {
      fetchFilteredProducts();
    }
  }, [loading, initialProducts, token]);

  // Get unique categories and filter reasons for filter dropdowns
  const categories = useMemo(() => {
    const cats = new Set(filteredProducts.map(p => p.category).filter(Boolean) as string[]);
    return Array.from(cats).sort();
  }, [filteredProducts]);

  const filterReasons = useMemo(() => {
    const reasons = new Set(filteredProducts.map(p => p.filter_reason));
    return Array.from(reasons).sort();
  }, [filteredProducts]);

  // Filter products based on search and filters
  const displayedProducts = useMemo(() => {
    return filteredProducts.filter(product => {
      const matchesSearch = !searchQuery || 
        product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.sku?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.source_url.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = categoryFilter === "all" || product.category === categoryFilter;
      const matchesReason = reasonFilter === "all" || product.filter_reason === reasonFilter;
      
      return matchesSearch && matchesCategory && matchesReason;
    });
  }, [filteredProducts, searchQuery, categoryFilter, reasonFilter]);

  // Handle selection
  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(displayedProducts.map(p => p.id)));
    }
    setSelectAll(!selectAll);
  };

  const toggleProductSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const isProductSelected = (id: number) => selectedIds.has(id);

  // Bulk actions
  const bulkActivate = async () => {
    if (!token || selectedIds.size === 0) return;
    setActionLoading(prev => new Set([...prev, ...selectedIds]));
    try {
      for (const id of selectedIds) {
        const response = await fetch(`/api/admin/products/${id}/activate`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) console.error(`Failed to activate product ${id}`);
      }
      setFilteredProducts(prev => prev.filter(p => !selectedIds.has(p.id)));
      setSelectedIds(new Set());
      setSelectAll(false);
    } catch (error) {
      console.error("Failed to bulk activate products:", error);
    } finally {
      setActionLoading(new Set());
    }
  };

  const bulkDelete = async () => {
    if (!token || selectedIds.size === 0) return;
    if (!confirm(`Permanently delete ${selectedIds.size} products? This cannot be undone.`)) return;
    
    setActionLoading(prev => new Set([...prev, ...selectedIds]));
    try {
      for (const id of selectedIds) {
        const response = await fetch(`/api/admin/products/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) console.error(`Failed to delete product ${id}`);
      }
      setFilteredProducts(prev => prev.filter(p => !selectedIds.has(p.id)));
      setSelectedIds(new Set());
      setSelectAll(false);
    } catch (error) {
      console.error("Failed to bulk delete products:", error);
    } finally {
      setActionLoading(new Set());
    }
  };

  // Single product actions
  const activateProduct = async (productId: number) => {
    if (!token) return;
    setActionLoading(prev => new Set([...prev, productId]));
    try {
      const response = await fetch(`/api/admin/products/${productId}/activate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        setFilteredProducts(prev => prev.filter(p => p.id !== productId));
      }
    } catch (error) {
      console.error("Failed to activate product:", error);
    } finally {
      setActionLoading(prev => { const next = new Set(prev); next.delete(productId); return next; });
    }
  };

  const deleteProduct = async (productId: number) => {
    if (!token) return;
    if (!confirm("Permanently delete this product? This cannot be undone.")) return;
    
    setActionLoading(prev => new Set([...prev, productId]));
    try {
      const response = await fetch(`/api/admin/products/${productId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        setFilteredProducts(prev => prev.filter(p => p.id !== productId));
      }
    } catch (error) {
      console.error("Failed to delete product:", error);
    } finally {
      setActionLoading(prev => { const next = new Set(prev); next.delete(productId); return next; });
    }
  };

  const isLoading = (id?: number) => id ? actionLoading.has(id) : actionLoading.size > 0;

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Filtered Products Review</h3>
          <p className="text-sm text-slate-500">
            {filteredProducts.length} total filtered products ({displayedProducts.length} displayed)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={fetchFilteredProducts}
            disabled={loading || !token}
            className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
          {selectedIds.size > 0 && (
            <>
              <button
                onClick={bulkActivate}
                disabled={isLoading() || !token}
                className="px-3 py-1.5 text-sm font-medium text-white bg-emerald-600 border border-transparent rounded-md hover:bg-emerald-700 disabled:opacity-50"
              >
                {isLoading() ? "Activating..." : `Activate Selection (${selectedIds.size})`}
              </button>
              <button
                onClick={bulkDelete}
                disabled={isLoading() || !token}
                className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {isLoading() ? "Deleting..." : `Delete Selection (${selectedIds.size})`}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3 p-3 bg-slate-50 rounded-md border border-slate-200">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder="Search by name, SKU, or URL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-sm"
          />
        </div>
        <div className="min-w-[180px]">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full text-sm rounded-md border border-slate-300 bg-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="all">All Categories</option>
            <option value="none">No Category</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
        <div className="min-w-[180px]">
          <select
            value={reasonFilter}
            onChange={(e) => setReasonFilter(e.target.value)}
            className="w-full text-sm rounded-md border border-slate-300 bg-white px-3 py-2 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="all">All Reasons</option>
            {filterReasons.map(reason => (
              <option key={reason} value={reason}>{reason}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <p className="text-sm text-slate-600">Loading...</p>}

      {!loading && displayedProducts.length === 0 && (
        <p className="text-sm text-slate-600 text-center py-8">
          {filteredProducts.length === 0 ? "No filtered products to review." : "No products match your filters."}
        </p>
      )}

      {!loading && displayedProducts.length > 0 && (
        <div className="space-y-2 max-h-[600px] overflow-y-auto border border-slate-200 rounded-md">
          {/* Header row */}
          <div className="grid grid-cols-[24px_1fr_auto_auto_auto_100px] gap-2 px-3 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider bg-slate-100 sticky top-0 z-10">
            <div></div>
            <div>Product</div>
            <div>Category</div>
            <div>Reason</div>
            <div>Price</div>
            <div className="text-right">Actions</div>
          </div>

          {/* Select all checkbox in header */}
          <div className="grid grid-cols-[24px_1fr_auto_auto_auto_100px] gap-2 px-3 py-2 border-t border-slate-200 bg-slate-50 sticky top-0 z-10">
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={selectAll && displayedProducts.length > 0}
                onChange={toggleSelectAll}
                disabled={displayedProducts.length === 0}
                aria-label="Select all displayed products"
                className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
            </div>
            <div className="text-sm text-slate-500">Select all {displayedProducts.length} displayed</div>
          </div>

          {/* Product rows */}
          {displayedProducts.map((product) => (
            <div
              key={product.id}
              className="grid grid-cols-[24px_1fr_auto_auto_auto_100px] gap-2 px-3 py-3 items-start gap-y-2 border-t border-slate-100 hover:bg-slate-50 transition-colors"
            >
              <div className="flex items-start pt-1">
                <input
                  type="checkbox"
                  checked={isProductSelected(product.id)}
                  onChange={() => toggleProductSelect(product.id)}
                  disabled={isLoading(product.id)}
                  aria-label={`Select ${product.name}`}
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium truncate">{product.name}</p>
                  <Badge variant={product.is_bundle ? "secondary" : "outline"} className="text-xs">
                    {product.is_bundle ? "Bundle" : "Home Page"}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mb-1">Reason: {product.filter_reason}</p>
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  {product.category && (
                    <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-700 rounded">
                      {product.category}
                    </span>
                  )}
                  <span className="font-semibold text-emerald-600">
                    AUD {product.price_aud.toFixed(2)}
                  </span>
                  <span className="text-slate-600">LKR {product.price_lkr.toFixed(2)}</span>
                  {product.sku && <span className="text-slate-500">SKU: {product.sku}</span>}
                </div>
                {product.image_url && (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="mt-2 h-20 w-auto rounded object-cover border border-slate-200"
                    loading="lazy"
                  />
                )}
              </div>

              <div className="hidden sm:block text-right text-sm text-slate-500">
                {product.category || <span className="text-slate-300">—</span>}
              </div>
              <div className="hidden sm:block text-right text-sm text-slate-500">
                {product.filter_reason}
              </div>
              <div className="hidden sm:block text-right text-sm">
                <span className="font-semibold text-emerald-600">AUD {product.price_aud.toFixed(2)}</span>
                <span className="text-slate-600 ml-1">LKR {product.price_lkr.toFixed(2)}</span>
              </div>
              <div className="flex gap-1 justify-end">
                <button
                  onClick={() => activateProduct(product.id)}
                  disabled={isLoading(product.id) || !token}
                  className="px-2 py-1 text-xs font-medium text-white bg-emerald-600 rounded hover:bg-emerald-700 disabled:opacity-50"
                >
                  {isLoading(product.id) ? "..." : "Activate"}
                </button>
                <button
                  onClick={() => deleteProduct(product.id)}
                  disabled={isLoading(product.id) || !token}
                  className="px-2 py-1 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50"
                >
                  {isLoading(product.id) ? "..." : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}