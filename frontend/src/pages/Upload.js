import React, { useState } from 'react';
import { documentService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, FileText } from 'lucide-react';
import { toast } from 'sonner';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
      ];
      if (validTypes.includes(selectedFile.type)) {
        setFile(selectedFile);
      } else {
        toast.error('Please upload PDF, DOCX, PPTX, or TXT files only');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const { data } = await documentService.upload(formData);
      toast.success('File uploaded successfully!');
      navigate(`/documents/${data.id}`);
    } catch (e) {
      toast.error('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen noise-overlay" style={{ background: 'var(--bg-main)' }}>
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#A2D2FF] rounded-2xl border-2 border-[#0A0A0A] neo-shadow mb-4">
            <UploadIcon className="w-8 h-8 text-[#0A0A0A]" strokeWidth={2.5} />
          </div>
          <h1 className="text-5xl font-black text-[#0A0A0A] tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Upload Study Material
          </h1>
          <p className="text-lg text-[#0A0A0A]" style={{ fontFamily: 'DM Sans, sans-serif' }}>
            Upload PDFs, Word docs, PowerPoints, or text files
          </p>
        </div>

        <div className="card" data-testid="upload-card">
          <div
            className="border-4 border-dashed border-[#0A0A0A] rounded-2xl p-12 text-center mb-6 bg-[#FDFBF7] transition-all hover:bg-white"
            onDrop={(e) => {
              e.preventDefault();
              const droppedFile = e.dataTransfer.files[0];
              if (droppedFile) {
                setFile(droppedFile);
              }
            }}
            onDragOver={(e) => e.preventDefault()}
          >
            {!file ? (
              <>
                <FileText className="w-16 h-16 text-[#0A0A0A] mx-auto mb-4 opacity-30" strokeWidth={2} />
                <p className="text-lg font-semibold text-[#0A0A0A] mb-2">Drag and drop your file here</p>
                <p className="text-sm text-[#0A0A0A] mb-4">or</p>
                <label className="btn-primary inline-block cursor-pointer" data-testid="select-file-btn">
                  Choose File
                  <input type="file" onChange={handleFileChange} className="hidden" accept=".pdf,.docx,.pptx,.txt" />
                </label>
                <p className="text-xs text-[#0A0A0A] mt-4">Supported: PDF, DOCX, PPTX, TXT (Max 50MB)</p>
              </>
            ) : (
              <div className="space-y-4">
                <FileText className="w-16 h-16 text-[#FF5722] mx-auto" strokeWidth={2.5} />
                <p className="text-lg font-semibold text-[#0A0A0A]">{file.name}</p>
                <p className="text-sm text-[#0A0A0A]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <button
                  onClick={() => setFile(null)}
                  className="text-sm font-semibold text-[#FF5722] underline"
                  data-testid="remove-file-btn"
                >
                  Remove file
                </button>
              </div>
            )}
          </div>

          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-primary w-full"
              data-testid="upload-btn"
            >
              {uploading ? 'Uploading...' : 'Upload & Process'}
            </button>
          )}
        </div>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { type: 'PDF', icon: '📄', color: '#FF5722' },
            { type: 'DOCX', icon: '📝', color: '#A2D2FF' },
            { type: 'PPTX', icon: '📊', color: '#CDB4DB' },
            { type: 'TXT', icon: '📃', color: '#FFC857' },
          ].map((format) => (
            <div
              key={format.type}
              className="p-4 bg-white rounded-xl border-2 border-[#0A0A0A] text-center"
            >
              <div className="text-3xl mb-2">{format.icon}</div>
              <p className="font-semibold text-[#0A0A0A]">{format.type}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Upload;
