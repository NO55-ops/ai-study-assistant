import React, { useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, FileText, ZoomIn, ZoomOut } from 'lucide-react';
import { documentService } from '../services/api';

const StudyWorkspace = ({ document, title, subtitle, children }) => {
  const [mobileOpen, setMobileOpen] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [pdfUrl, setPdfUrl] = useState(null);

  const mimeType = typeof document?.content_type === 'string' ? document.content_type.toLowerCase() : '';
  const fileName = typeof document?.original_filename === 'string' ? document.original_filename.toLowerCase() : '';
  const isPdf = mimeType.includes('pdf') || fileName.endsWith('.pdf');

  useEffect(() => {
    let active = true;
    let objectUrl = null;

    if (!document?.id || !isPdf) {
      setPdfUrl(null);
      return undefined;
    }

    documentService.getFile(document.id)
      .then(({ data }) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(data);
        setPdfUrl((current) => {
          if (current) {
            URL.revokeObjectURL(current);
          }
          return objectUrl;
        });
      })
      .catch(() => {
        if (active) {
          setPdfUrl(null);
        }
      });

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [document?.id, isPdf]);

  const preview = useMemo(() => {
    if (!document) {
      return 'Select a document to keep it visible while you study, quiz, and ask the tutor questions.';
    }

    if (isPdf) {
      return '';
    }

    const sourceText = document.extracted_text || document.summary || '';
    if (!sourceText) {
      return 'This document is ready for study mode.';
    }

    const compactText = sourceText.replace(/\s+/g, ' ').trim();
    return compactText.length > 1800 ? `${compactText.slice(0, 1800)}...` : compactText;
  }, [document, isPdf]);

  return (
    <div className="study-workspace" data-testid="study-workspace">
      <aside className={`study-workspace__sidebar ${mobileOpen ? 'open' : 'collapsed'}`}>
        <div className="study-workspace__sidebar-header">
          <div className="study-workspace__icon-wrap">
            <FileText className="study-workspace__icon" strokeWidth={2.5} />
          </div>
          <div>
            <p className="study-workspace__eyebrow">Source Document</p>
            <h3 className="study-workspace__title">
              {document?.original_filename || document?.name || title || 'No document selected'}
            </h3>
          </div>
        </div>

        <div className="study-workspace__meta">
          {document ? (
            <>
              <span>{document.content_type || 'document'}</span>
              {document.created_at && (
                <span>{new Date(document.created_at).toLocaleDateString()}</span>
              )}
            </>
          ) : (
            <span>No document loaded</span>
          )}
        </div>

        {isPdf && pdfUrl ? (
          <div className="study-workspace__pdf-panel">
            <div className="study-workspace__pdf-toolbar">
              <button type="button" onClick={() => setZoomLevel((value) => Math.max(70, value - 10))} aria-label="Zoom out">
                <ZoomOut size={16} />
              </button>
              <span>{zoomLevel}%</span>
              <button type="button" onClick={() => setZoomLevel((value) => Math.min(200, value + 10))} aria-label="Zoom in">
                <ZoomIn size={16} />
              </button>
            </div>

            <div className="study-workspace__pdf-scroll">
              <iframe
                src={pdfUrl}
                title={document?.original_filename || 'Study document'}
                className="study-workspace__pdf-frame"
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
              />
            </div>
          </div>
        ) : (
          <div className="study-workspace__preview">
            {preview ? <p>{preview}</p> : <p className="study-workspace__empty">No document preview available.</p>}
          </div>
        )}

        {document && (
          <div className="study-workspace__footer">
            <span className="badge badge-mint">Ready to study</span>
          </div>
        )}
      </aside>

      <div className="study-workspace__content">
        <div className="study-workspace__mobile-toggle">
          <button type="button" onClick={() => setMobileOpen((value) => !value)}>
            {mobileOpen ? 'Hide document' : 'Show document'}
            {mobileOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {subtitle && <p className="study-workspace__subtitle">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
};

export default StudyWorkspace;
