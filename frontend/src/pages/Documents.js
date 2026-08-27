import React, { useEffect, useState, useCallback } from 'react';
import { documentService } from '../services/api';
import { Link } from 'react-router-dom';
import { FileText, Trash2, Eye } from 'lucide-react';
import { toast } from 'sonner';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    try {
      const { data } = await documentService.list();
      setDocuments(data);
    } catch (e) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;

    try {
      await documentService.delete(id);
      toast.success('Document deleted');
      fetchDocuments();
    } catch (e) {
      toast.error('Failed to delete document');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--bg-main)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#FF5722] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-[#0A0A0A] font-semibold">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              My Documents
            </h1>
            <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
              {documents.length} {documents.length === 1 ? 'document' : 'documents'} uploaded
            </p>
          </div>
          <Link to="/upload" className="btn-primary" data-testid="upload-new-btn">
            Upload New
          </Link>
        </div>

        {documents.length === 0 ? (
          <div className="card text-center py-16" data-testid="empty-docs-state">
            <FileText className="w-24 h-24 text-[#0A0A0A] mx-auto mb-6 opacity-20" strokeWidth={1.5} />
            <h2 className="text-2xl font-black text-[#0A0A0A] mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              No documents yet
            </h2>
            <p className="text-[#0A0A0A] mb-6">Upload your first study material to get started</p>
            <Link to="/upload" className="btn-primary inline-block">
              Upload Document
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc, idx) => (
              <div key={doc.id} className="card animate-fade-up" style={{ animationDelay: `${idx * 0.1}s` }} data-testid={`doc-card-${idx}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-[#A2D2FF] rounded-xl flex items-center justify-center border-2 border-[#0A0A0A]">
                    <FileText className="w-6 h-6 text-[#0A0A0A]" strokeWidth={2.5} />
                  </div>
                  <span className="badge badge-mint">
                    {doc.content_type?.includes('pdf')
                      ? 'PDF'
                      : doc.content_type?.includes('word')
                      ? 'DOCX'
                      : doc.content_type?.includes('presentation')
                      ? 'PPTX'
                      : 'TXT'}
                  </span>
                </div>
                <h3 className="font-bold text-[#0A0A0A] mb-2 truncate" title={doc.original_filename}>
                  {doc.original_filename}
                </h3>
                <p className="text-xs text-[#0A0A0A] mb-4">
                  Uploaded {new Date(doc.created_at).toLocaleDateString()}
                </p>
                <div className="flex gap-2">
                  <Link
                    to={`/documents/${doc.id}`}
                    className="btn-secondary flex-1 py-2 px-4 text-sm flex items-center justify-center gap-2"
                    data-testid={`view-doc-${idx}-btn`}
                  >
                    <Eye className="w-4 h-4" />
                    View
                  </Link>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 bg-[#FF865E] text-[#0A0A0A] rounded-xl border-2 border-[#0A0A0A] hover:-translate-y-1 hover:neo-shadow transition-all"
                    data-testid={`delete-doc-${idx}-btn`}
                  >
                    <Trash2 className="w-4 h-4" strokeWidth={2.5} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Documents;
