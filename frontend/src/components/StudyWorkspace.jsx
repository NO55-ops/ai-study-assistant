import React, { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

const StudyWorkspace = ({ document, title, subtitle, children }) => {
  const [mobileOpen, setMobileOpen] = useState(true);

  const preview = useMemo(() => {
    if (!document) {
      return 'Select a document to keep it visible while you study, quiz, and ask the tutor questions.';
    }

    const sourceText = document.extracted_text || document.summary || '';
    if (!sourceText) {
      return 'This document has been uploaded and is ready for study mode. Use the tools on the right to generate a quiz, review flashcards, or ask the tutor.';
    }

    const compactText = sourceText.replace(/\s+/g, ' ').trim();
    return compactText.length > 1800 ? `${compactText.slice(0, 1800)}...` : compactText;
  }, [document]);

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
              {document?.original_filename || title || 'No document selected'}
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

        <div className="study-workspace__preview">
          <p>{preview}</p>
        </div>

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
