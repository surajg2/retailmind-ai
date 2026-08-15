import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Search,
  Plus,
  Edit2,
  Trash2,
  AlertCircle,
  Filter,
  CheckCircle2,
  X,
  ExternalLink,
  Database
} from 'lucide-react';
import { productsApi, ProductItem } from '../services/api';

export const ProductsPage: React.FC = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [includeInactive, setIncludeInactive] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Add Product Modal State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newSku, setNewSku] = useState<string>('');
  const [newName, setNewName] = useState<string>('');
  const [newCat, setNewCat] = useState<string>('General');
  const [newUnit, setNewUnit] = useState<string>('pcs');
  const [newCost, setNewCost] = useState<string>('0.00');
  const [newPrice, setNewPrice] = useState<string>('0.00');
  const [newMinStock, setNewMinStock] = useState<number>(10);
  const [modalError, setModalError] = useState<string | null>(null);

  // Edit Product Modal State
  const [editingProduct, setEditingProduct] = useState<ProductItem | null>(null);

  useEffect(() => {
    fetchProducts();
  }, [search, category, includeInactive]);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await productsApi.listProducts({
        search: search || undefined,
        category: category || undefined,
        include_inactive: includeInactive,
        limit: 100
      });
      setProducts(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load products.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    try {
      await productsApi.createProduct({
        sku: newSku,
        name: newName,
        category: newCat,
        unit: newUnit,
        cost_price: Number(newCost),
        selling_price: Number(newPrice),
        min_stock_level: newMinStock
      });
      setShowAddModal(false);
      resetForm();
      fetchProducts();
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to create product.');
    }
  };

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    try {
      await productsApi.updateProduct(editingProduct.id, {
        name: editingProduct.name,
        category: editingProduct.category || 'General',
        unit: editingProduct.unit,
        cost_price: editingProduct.cost_price as any,
        selling_price: editingProduct.selling_price as any,
        min_stock_level: editingProduct.min_stock_level,
        is_active: editingProduct.is_active
      });
      setEditingProduct(null);
      fetchProducts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update product.');
    }
  };

  const handleSoftDeactivate = async (product: ProductItem) => {
    if (!window.confirm(`Are you sure you want to soft-deactivate product '${product.name}' (SKU: ${product.sku})?\n\nThis hides the product from the active catalog view, but preserves all historical sales records intact.`)) {
      return;
    }
    try {
      await productsApi.deactivateProduct(product.id);
      fetchProducts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to deactivate product.');
    }
  };

  const resetForm = () => {
    setNewSku('');
    setNewName('');
    setNewCat('General');
    setNewUnit('pcs');
    setNewCost('0.00');
    setNewPrice('0.00');
    setNewMinStock(10);
  };

  return (
    <div className="page-data-wipe space-y-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Product Catalog Management
          </h1>
          <p className="text-zinc-400 text-xs sm:text-sm mt-1">
            Manage catalog items, stock thresholds, pricing, and active status
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="tactile-button flex items-center gap-2 px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-bold transition-all shadow-md"
        >
          <Plus className="w-4 h-4" /> Add New Product
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 backdrop-blur-sm">
        
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by SKU or Product Name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-zinc-950 text-zinc-200 text-xs rounded-lg pl-9 pr-4 py-2 border border-zinc-800 focus:outline-none focus:border-zinc-500 transition-colors"
          />
        </div>

        {/* Category & Inactive Toggle */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-300 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded bg-zinc-950 border-zinc-700 text-zinc-300 focus:ring-0"
            />
            <span>Include Soft-Deactivated</span>
          </label>
        </div>

      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3 text-rose-400 text-xs">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Products Data Table with Group Materialization */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-zinc-400 border-b border-zinc-800 bg-zinc-950/80">
                <th className="py-3 px-4 font-semibold">SKU</th>
                <th className="py-3 px-4 font-semibold">Product Name</th>
                <th className="py-3 px-4 font-semibold">Category</th>
                <th className="py-3 px-4 font-semibold">Selling Price</th>
                <th className="py-3 px-4 font-semibold">Cost Price</th>
                <th className="py-3 px-4 font-semibold">Min Stock Level</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {products.map((p, idx) => {
                const batchClass = idx < 3 ? 'materialize-batch-1' : (idx < 7 ? 'materialize-batch-2' : (idx < 12 ? 'materialize-batch-3' : 'materialize-batch-4'));
                return (
                  <tr key={p.id} className={`${batchClass} hover:bg-zinc-800/40 transition-colors ${!p.is_active ? 'opacity-60 bg-zinc-950/40' : ''}`}>
                    <td className="py-3 px-4 font-mono font-semibold text-zinc-200">{p.sku}</td>
                    <td className="py-3 px-4 font-medium text-zinc-200">{p.name}</td>
                    <td className="py-3 px-4 text-zinc-400">{p.category || 'General'}</td>
                    <td className="py-3 px-4 font-semibold text-emerald-400 font-mono">₹{Number(p.selling_price).toFixed(2)}</td>
                    <td className="py-3 px-4 text-zinc-400 font-mono">₹{Number(p.cost_price).toFixed(2)}</td>
                    <td className="py-3 px-4 text-zinc-300 font-mono">{p.min_stock_level} {p.unit}</td>
                    <td className="py-3 px-4">
                      {p.is_active ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate(`/products/${p.id}`)}
                          className="tactile-button p-1.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setEditingProduct(p)}
                          className="tactile-button p-1.5 text-zinc-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                          title="Edit Product"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        {p.is_active && (
                          <button
                            onClick={() => handleSoftDeactivate(p)}
                            className="tactile-button p-1.5 text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                            title="Soft Deactivate (Preserves Sales History)"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {products.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="py-8 text-center">
                    <div className="empty-data-grid py-8 rounded-xl border border-zinc-800/80 flex flex-col items-center justify-center text-zinc-400">
                      <Database className="w-6 h-6 text-zinc-500 mb-1.5" />
                      <span className="text-xs font-semibold text-zinc-300">No products found matching query</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-zinc-950/85 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Add New Product</h3>
              <button onClick={() => setShowAddModal(false)} className="text-zinc-400 hover:text-zinc-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 mb-4 text-xs text-rose-400">
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateProduct} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-zinc-300 mb-1 block">SKU Code *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SKU-GROC-099"
                  value={newSku}
                  onChange={(e) => setNewSku(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-zinc-300 mb-1 block">Product Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Sunflower Oil 1L"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Category</label>
                  <input
                    type="text"
                    value={newCat}
                    onChange={(e) => setNewCat(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Unit</label>
                  <input
                    type="text"
                    value={newUnit}
                    onChange={(e) => setNewUnit(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Selling Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newPrice}
                    onChange={(e) => setNewPrice(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newCost}
                    onChange={(e) => setNewCost(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="tactile-button px-4 py-2 bg-zinc-800 text-zinc-300 rounded-xl text-xs font-semibold hover:bg-zinc-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="tactile-button px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-bold shadow-md"
                >
                  Create Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Product Modal */}
      {editingProduct && (
        <div className="fixed inset-0 z-50 bg-zinc-950/85 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Edit Product (SKU: {editingProduct.sku})</h3>
              <button onClick={() => setEditingProduct(null)} className="text-zinc-400 hover:text-zinc-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateProduct} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-zinc-300 mb-1 block">Product Name</label>
                <input
                  type="text"
                  value={editingProduct.name}
                  onChange={(e) => setEditingProduct({ ...editingProduct, name: e.target.value })}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Category</label>
                  <input
                    type="text"
                    value={editingProduct.category || ''}
                    onChange={(e) => setEditingProduct({ ...editingProduct, category: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-zinc-300 mb-1 block">Selling Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editingProduct.selling_price}
                    onChange={(e) => setEditingProduct({ ...editingProduct, selling_price: e.target.value })}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-200 focus:border-zinc-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingProduct(null)}
                  className="tactile-button px-4 py-2 bg-zinc-800 text-zinc-300 rounded-xl text-xs font-semibold hover:bg-zinc-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="tactile-button px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-bold shadow-md"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
