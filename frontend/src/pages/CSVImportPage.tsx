import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';
import { api, CSVImportResult } from '../services/api';

export const CSVImportPage: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [result, setResult] = useState<CSVImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post<CSVImportResult>('/api/v1/sales/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'CSV Upload failed due to a server error.');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateSynthetic = async () => {
    setGenerating(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.post('/api/v1/sales/generate-synthetic');
      if (response.data.success) {
        setResult({
          success: true,
          total_rows_processed: response.data.records_generated,
          successful_imports: response.data.imported_count,
          errors: [],
          message: response.data.message
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Synthetic dataset generation failed.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="page-data-wipe max-w-3xl mx-auto space-y-6 pb-12">
      
      {/* Page Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Sales CSV Data Ingestion Engine
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm mt-1">
          Atomic 2-Phase Validation: Upload daily sales CSVs with zero-partial-write guarantee
        </p>
      </div>

      {/* CSV Specification Guidance */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
        <h3 className="text-sm font-semibold text-cyan-400 mb-2 flex items-center gap-2">
          <FileText className="w-4 h-4" /> Required CSV Header Format
        </h3>
        <div className="bg-slate-950 p-3 rounded-xl font-mono text-[11px] text-slate-300 border border-slate-800 overflow-x-auto">
          date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
        </div>
        <ul className="text-xs text-slate-400 mt-3 space-y-1 list-disc list-inside">
          <li>Supports comment lines starting with <code className="text-cyan-400">#</code>.</li>
          <li>If ANY validation error occurs on any row, <strong>ZERO rows are inserted</strong> into PostgreSQL.</li>
          <li>Dates must follow <code className="text-cyan-400">YYYY-MM-DD</code> format.</li>
        </ul>
      </div>

      {/* Action Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Card 1: Custom CSV Upload */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <UploadCloud className="w-5 h-5 text-cyan-400" />
              <h3 className="text-base font-bold text-white">Upload Custom CSV</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Upload your store's sales records CSV for automated normalization and DB ingestion.
            </p>

            <form onSubmit={handleUpload} className="space-y-4">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full bg-slate-950 text-xs text-slate-300 border border-slate-800 rounded-xl p-2.5 file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/10 file:text-cyan-400 hover:file:bg-cyan-500/20"
              />

              <button
                type="submit"
                disabled={!file || uploading}
                className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
              >
                {uploading ? 'Validating & Importing...' : 'Validate & Import CSV'}
              </button>
            </form>
          </div>
        </div>

        {/* Card 2: Generate 7,300 Synthetic Dataset */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <h3 className="text-base font-bold text-white">Seed 7,300 Synthetic Dataset</h3>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Automatically generate and ingest a 7,300-record daily dataset (20 Kirana products $\times$ 365 days) featuring weekly seasonality, regional festival uplifts, and probabilistic stockouts.
            </p>

            <button
              onClick={handleGenerateSynthetic}
              disabled={generating}
              className="w-full py-2.5 bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50"
            >
              {generating ? 'Generating 7,300 Records...' : 'Generate 7,300 Synthetic Sales'}
            </button>
          </div>
        </div>

      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 flex items-center gap-3 text-rose-400 text-xs">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className={`border rounded-2xl p-5 shadow-xl backdrop-blur-md ${
          result.success ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-rose-500/10 border-rose-500/30'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {result.success ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              )}
              <h3 className={`text-sm font-bold ${result.success ? 'text-emerald-400' : 'text-rose-400'}`}>
                {result.success ? 'Import Completed Successfully' : 'Import Rejected (Zero Rows Inserted)'}
              </h3>
            </div>
            <span className="text-xs font-medium text-slate-300">
              Processed: {result.total_rows_processed} rows | Imported: {result.successful_imports}
            </span>
          </div>

          <p className="text-xs text-slate-300 mb-4">{result.message}</p>

          {/* Validation Errors List */}
          {result.errors.length > 0 && (
            <div className="bg-slate-950/80 rounded-xl p-4 border border-rose-500/20 max-h-60 overflow-y-auto space-y-2">
              <h4 className="text-xs font-semibold text-rose-400 mb-2">Detailed Row Validation Errors:</h4>
              {result.errors.map((err: { row_number: number; error: string }, idx: number) => (
                <div key={idx} className="text-[11px] text-slate-300 flex items-start gap-2 font-mono border-b border-slate-900 pb-1.5">
                  <span className="text-rose-400 font-bold">Row {err.row_number}:</span>
                  <span>{err.error}</span>
                </div>
              ))}
            </div>
          )}

          {result.success && (
            <div className="mt-4 text-right">
              <button
                onClick={() => navigate('/')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md"
              >
                Go to Sales Analytics Dashboard <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
