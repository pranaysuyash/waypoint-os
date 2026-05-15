'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  type BookingDocument,
  type BookingTraveler,
  type ExtractionResponse,
  getDocuments,
  uploadDocument,
  acceptDocument,
  rejectDocument,
  deleteDocument,
  getDocumentDownloadUrl,
  extractDocument,
  applyExtraction,
  rejectExtraction,
} from '@/lib/api-client';
import { ExtractionHistoryPanel } from '@/components/workspace/panels/ExtractionHistoryPanel';

interface DocumentsZoneProps {
  tripId: string;
  canUpload: boolean;
  travelers?: BookingTraveler[];
  onDocumentsChange?: (docs: BookingDocument[]) => void;
}

export default function DocumentsZone({ tripId, canUpload, travelers = [], onDocumentsChange }: DocumentsZoneProps) {
  const [documents, setDocuments] = useState<BookingDocument[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docUploading, setDocUploading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string>('passport');
  const [docActionLoading, setDocActionLoading] = useState<string | null>(null);

  const [extractions, setExtractions] = useState<Record<string, ExtractionResponse>>({});
  const [extractingDocId, setExtractingDocId] = useState<string | null>(null);
  const [extractionAction, setExtractionAction] = useState<string | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [extractionSelections, setExtractionSelections] = useState<Record<string, {
    travelerId: string;
    selectedFields: string[];
  }>>({});
  const [extractionConflicts, setExtractionConflicts] = useState<Record<string, Array<{
    field_name: string;
    existing_value: string;
    extracted_value: string;
  }>>>({});

  const fetchDocuments = useCallback(async () => {
    setDocsLoading(true);
    try {
      const resp = await getDocuments(tripId);
      setDocuments(resp.documents);
      onDocumentsChange?.(resp.documents);
    } catch {
      // No documents is fine
    } finally {
      setDocsLoading(false);
    }
  }, [tripId, onDocumentsChange]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDocUpload = useCallback(async () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      setDocUploading(true);
      setDocError(null);
      try {
        await uploadDocument(tripId, file, uploadDocType);
        await fetchDocuments();
      } catch (e) {
        setDocError(e instanceof Error ? e.message : 'Upload failed');
      } finally {
        setDocUploading(false);
      }
    };
    input.click();
  }, [tripId, uploadDocType, fetchDocuments]);

  const handleDocDownload = useCallback(async (docId: string) => {
    try {
      const { url } = await getDocumentDownloadUrl(tripId, docId);
      const fullUrl = url.startsWith('/') ? `${window.location.origin}${url}` : url;
      window.open(fullUrl, '_blank');
    } catch {
      setDocError('Failed to get download URL');
    }
  }, [tripId]);

  const handleDocAccept = useCallback(async (docId: string) => {
    setDocActionLoading(docId);
    try {
      await acceptDocument(tripId, docId);
      await fetchDocuments();
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Accept failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [tripId, fetchDocuments]);

  const handleDocReject = useCallback(async (docId: string) => {
    setDocActionLoading(docId);
    try {
      await rejectDocument(tripId, docId);
      await fetchDocuments();
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Reject failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [tripId, fetchDocuments]);

  const handleDocDelete = useCallback(async (docId: string) => {
    setDocActionLoading(docId);
    try {
      await deleteDocument(tripId, docId);
      await fetchDocuments();
      setExtractions((prev) => { const n = { ...prev }; delete n[docId]; return n; });
      setExtractionSelections((prev) => { const n = { ...prev }; delete n[docId]; return n; });
      setExtractionConflicts((prev) => { const n = { ...prev }; delete n[docId]; return n; });
    } catch (e) {
      setDocError(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDocActionLoading(null);
    }
  }, [tripId, fetchDocuments]);

  const handleExtract = useCallback(async (docId: string) => {
    setExtractingDocId(docId);
    setExtractionError(null);
    try {
      const resp = await extractDocument(tripId, docId);
      setExtractions((prev) => ({ ...prev, [docId]: resp }));
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Extraction failed');
    } finally {
      setExtractingDocId(null);
    }
  }, [tripId]);

  const handleApplyExtraction = useCallback(async (docId: string, travelerId: string, fields: string[], allowOverwrite = false) => {
    setExtractionAction(docId);
    setExtractionError(null);
    try {
      const resp = await applyExtraction(tripId, docId, {
        traveler_id: travelerId,
        fields_to_apply: fields,
        allow_overwrite: allowOverwrite,
      });
      if (resp.applied) {
        if (resp.extraction) {
          setExtractions((prev) => ({ ...prev, [docId]: resp.extraction! }));
        }
        setExtractionConflicts((prev) => { const n = { ...prev }; delete n[docId]; return n; });
      } else if (resp.conflicts.length > 0) {
        setExtractionConflicts((prev) => ({ ...prev, [docId]: resp.conflicts }));
      }
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Apply failed');
    } finally {
      setExtractionAction(null);
    }
  }, [tripId]);

  const handleRejectExtraction = useCallback(async (docId: string) => {
    setExtractionAction(docId);
    setExtractionError(null);
    try {
      const resp = await rejectExtraction(tripId, docId);
      setExtractions((prev) => ({ ...prev, [docId]: resp }));
    } catch (e) {
      setExtractionError(e instanceof Error ? e.message : 'Reject failed');
    } finally {
      setExtractionAction(null);
    }
  }, [tripId]);

  return (
    <div data-testid="ops-documents" className="border border-[#30363d] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-[#e6edf3]">Documents</h4>
        {canUpload && (
          <div className="flex items-center gap-2">
            <select
              value={uploadDocType}
              onChange={(e) => setUploadDocType(e.target.value)}
              className="bg-[#0d1117] border border-[#30363d] rounded px-2 py-1 text-xs text-[#e6edf3]"
            >
              <option value="passport">Passport</option>
              <option value="visa">Visa</option>
              <option value="insurance">Insurance</option>
              <option value="flight_ticket">Flight Ticket</option>
              <option value="hotel_confirmation">Hotel Confirmation</option>
              <option value="other">Other</option>
            </select>
            <button
              data-testid="ops-document-upload-btn"
              className="text-xs px-3 py-1 rounded bg-blue-900/50 text-blue-300 hover:bg-blue-800/50 disabled:opacity-50"
              onClick={handleDocUpload}
              disabled={docUploading}
            >
              {docUploading ? 'Uploading…' : 'Upload'}
            </button>
          </div>
        )}
      </div>

      {docError && (
        <div className="mb-3 text-xs text-red-400">{docError}</div>
      )}

      {docsLoading && (
        <span className="text-xs text-[#8b949e]">Loading documents…</span>
      )}

      {!docsLoading && documents.length === 0 && (
        <span className="text-xs text-[#8b949e]">No documents uploaded yet.</span>
      )}

      {!docsLoading && documents.length > 0 && (
        <div data-testid="ops-document-list" className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              data-testid={`ops-document-${doc.id}`}
              className="flex items-center justify-between py-2 px-3 rounded border border-[#30363d]"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-[#e6edf3]">
                  {doc.document_type.replace('_', ' ')}
                </span>
                <span className="text-xs text-[#8b949e]">
                  {doc.filename_ext} · {(doc.size_bytes / 1024).toFixed(0)}KB
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded ${
                    doc.status === 'pending_review'
                      ? 'bg-amber-900/50 text-amber-300'
                      : doc.status === 'accepted'
                        ? 'bg-emerald-900/50 text-emerald-300'
                        : doc.status === 'rejected'
                          ? 'bg-red-900/50 text-red-300'
                          : 'bg-[#30363d] text-[#8b949e]'
                  }`}
                >
                  {doc.status.replace('_', ' ')}
                </span>
                {doc.uploaded_by_type === 'customer' && (
                  <span className="text-xs px-2 py-0.5 rounded bg-blue-900/50 text-blue-300">
                    Customer
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                {doc.status === 'pending_review' && (
                  <>
                    <button
                      data-testid={`ops-document-${doc.id}-accept-btn`}
                      className="text-xs px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50 disabled:opacity-50"
                      onClick={() => handleDocAccept(doc.id)}
                      disabled={docActionLoading === doc.id}
                    >
                      Accept
                    </button>
                    <button
                      data-testid={`ops-document-${doc.id}-reject-btn`}
                      className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                      onClick={() => handleDocReject(doc.id)}
                      disabled={docActionLoading === doc.id}
                    >
                      Reject
                    </button>
                  </>
                )}
                {doc.status === 'accepted' && (
                  <>
                    <button
                      data-testid={`ops-document-${doc.id}-download-btn`}
                      className="text-xs px-2 py-1 rounded bg-[#30363d] text-[#e6edf3] hover:bg-[#484f58]"
                      onClick={() => handleDocDownload(doc.id)}
                    >
                      Download
                    </button>
                    <button
                      data-testid={`ops-document-${doc.id}-delete-btn`}
                      className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                      onClick={() => handleDocDelete(doc.id)}
                      disabled={docActionLoading === doc.id}
                    >
                      Delete
                    </button>
                  </>
                )}
                {doc.status === 'rejected' && (
                  <button
                    data-testid={`ops-document-${doc.id}-delete-btn`}
                    className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                    onClick={() => handleDocDelete(doc.id)}
                    disabled={docActionLoading === doc.id}
                  >
                    Delete
                  </button>
                )}
                {/* Extract button (pending_review or accepted) */}
                {(doc.status === 'pending_review' || doc.status === 'accepted') && !extractions[doc.id] && (
                  <button
                    data-testid={`ops-doc-extract-btn-${doc.id}`}
                    className="text-xs px-2 py-1 rounded bg-purple-900/50 text-purple-300 hover:bg-purple-800/50 disabled:opacity-50"
                    onClick={() => handleExtract(doc.id)}
                    disabled={extractingDocId === doc.id}
                  >
                    {extractingDocId === doc.id ? 'Extracting…' : 'Extract'}
                  </button>
                )}
              </div>
              {/* Extraction results */}
              {extractions[doc.id] && (
                <div data-testid={`ops-extraction-${doc.id}`} className="mt-2 border-t border-[#30363d] pt-2 space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-[#8b949e]">Extraction:</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      extractions[doc.id].status === 'applied' ? 'bg-emerald-900/50 text-emerald-300' :
                      extractions[doc.id].status === 'rejected' ? 'bg-red-900/50 text-red-300' :
                      'bg-yellow-900/50 text-yellow-300'
                    }`}>
                      {extractions[doc.id].status.replace('_', ' ')}
                    </span>
                    {extractions[doc.id].overall_confidence !== null && (
                      <span className="text-[#8b949e]">
                        confidence: {Math.round(extractions[doc.id].overall_confidence! * 100)}%
                      </span>
                    )}
                  </div>
                  <div data-testid={`ops-extraction-fields-${doc.id}`} className="space-y-1">
                    {extractions[doc.id].fields.flatMap((f) => f.present ? [(
                      <div key={f.field_name} className="flex items-center gap-2 text-xs">
                        {extractions[doc.id].status === 'pending_review' && (
                          <input
                            type="checkbox"
                            data-testid={`ops-extraction-field-cb-${doc.id}-${f.field_name}`}
                            checked={extractionSelections[doc.id]?.selectedFields.includes(f.field_name) ?? false}
                            onChange={(e) => {
                              setExtractionSelections((prev) => {
                                const cur = prev[doc.id] ?? { travelerId: '', selectedFields: [] };
                                const fields = e.target.checked
                                  ? [...cur.selectedFields, f.field_name]
                                  : cur.selectedFields.filter((s) => s !== f.field_name);
                                return { ...prev, [doc.id]: { ...cur, selectedFields: fields } };
                              });
                            }}
                            className="accent-purple-400"
                          />
                        )}
                        <span className="text-[#8b949e] w-32">{f.field_name.replace(/_/g, ' ')}:</span>
                        <span className="text-[#e6edf3]">{f.value ?? '-'}</span>
                        <span className={`text-[10px] px-1 rounded ${
                          f.confidence >= 0.9 ? 'text-emerald-400' :
                          f.confidence >= 0.7 ? 'text-yellow-400' :
                          'text-red-400'
                        }`}>
                          {Math.round(f.confidence * 100)}%
                        </span>
                      </div>
                    )] : [])}
                  </div>
                  {extractions[doc.id].status === 'pending_review' && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-[#8b949e]">Apply to:</span>
                        <select
                          data-testid={`ops-extraction-traveler-select-${doc.id}`}
                          value={extractionSelections[doc.id]?.travelerId ?? ''}
                          onChange={(e) => {
                            setExtractionSelections((prev) => {
                              const cur = prev[doc.id] ?? { travelerId: '', selectedFields: [] };
                              return { ...prev, [doc.id]: { ...cur, travelerId: e.target.value } };
                            });
                          }}
                          className="bg-[#0d1117] border border-[#30363d] rounded text-[#e6edf3] px-2 py-1 text-xs"
                        >
                          <option value="">Select traveler</option>
                          {travelers.map((t) => (
                            <option key={t.traveler_id} value={t.traveler_id}>
                              {t.traveler_id}{t.full_name ? ` - ${t.full_name}` : ''}
                            </option>
                          ))}
                        </select>
                      </div>
                      {extractionConflicts[doc.id] && extractionConflicts[doc.id].length > 0 && (
                        <div data-testid={`ops-extraction-conflicts-${doc.id}`} className="text-xs space-y-1 bg-yellow-900/20 border border-yellow-800/30 rounded p-2">
                          <div className="text-yellow-300 font-medium">Conflicts detected:</div>
                          {extractionConflicts[doc.id].map((c) => (
                            <div key={c.field_name} className="text-yellow-200">
                              {c.field_name.replace(/_/g, ' ')}: {c.existing_value} → {c.extracted_value}
                            </div>
                          ))}
                          <button
                            data-testid={`ops-extraction-overwrite-btn-${doc.id}`}
                            className="text-xs px-2 py-1 rounded bg-yellow-900/50 text-yellow-300 hover:bg-yellow-800/50 mt-1"
                            onClick={() => {
                              const sel = extractionSelections[doc.id];
                              if (sel && sel.travelerId && sel.selectedFields.length > 0) {
                                handleApplyExtraction(doc.id, sel.travelerId, sel.selectedFields, true);
                              }
                            }}
                            disabled={extractionAction === doc.id}
                          >
                            {extractionAction === doc.id ? 'Overwriting…' : 'Apply with overwrite'}
                          </button>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <button
                          data-testid={`ops-extraction-apply-btn-${doc.id}`}
                          className="text-xs px-2 py-1 rounded bg-emerald-900/50 text-emerald-300 hover:bg-emerald-800/50 disabled:opacity-50"
                          onClick={() => {
                            const sel = extractionSelections[doc.id];
                            if (sel?.travelerId && sel.selectedFields.length > 0) {
                              handleApplyExtraction(doc.id, sel.travelerId, sel.selectedFields, false);
                            }
                          }}
                          disabled={
                            extractionAction === doc.id ||
                            !extractionSelections[doc.id]?.travelerId ||
                            !(extractionSelections[doc.id]?.selectedFields.length > 0)
                          }
                        >
                          {extractionAction === doc.id ? 'Applying…' : 'Apply selected'}
                        </button>
                        <button
                          data-testid={`ops-extraction-reject-btn-${doc.id}`}
                          className="text-xs px-2 py-1 rounded bg-red-900/50 text-red-300 hover:bg-red-800/50 disabled:opacity-50"
                          onClick={() => handleRejectExtraction(doc.id)}
                          disabled={extractionAction === doc.id}
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  )}
                  {extractionError && extractionAction === doc.id && (
                    <div className="text-xs text-red-400">{extractionError}</div>
                  )}
                </div>
              )}
              {extractions[doc.id] && (
                <ExtractionHistoryPanel
                  tripId={tripId}
                  documentId={doc.id}
                  extraction={extractions[doc.id]}
                  onRetryComplete={(updated) => {
                    setExtractions((prev) => ({ ...prev, [doc.id]: updated }));
                  }}
                />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
