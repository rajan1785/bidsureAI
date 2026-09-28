"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export type ViewableDocument = { id: number; filename: string; doc_type?: string };

type ViewerContext = {
  /** Open the original bidder document in the shared viewer. */
  open: (doc: ViewableDocument) => void;
  /** Documents on the current bid, keyed lookup for rule/record linking. */
  byDocType: (docType: string | null | undefined) => ViewableDocument | null;
};

const DocumentViewerContext = createContext<ViewerContext | null>(null);

export function useDocumentViewer() {
  const ctx = useContext(DocumentViewerContext);
  if (!ctx) throw new Error("useDocumentViewer must be used inside <DocumentViewerProvider>");
  return ctx;
}

export function DocumentViewerProvider({
  documents,
  children,
}: {
  documents: ViewableDocument[];
  children: React.ReactNode;
}) {
  const [doc, setDoc] = useState<ViewableDocument | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [error, setError] = useState("");

  // The file endpoint is bearer-protected, so it cannot be used as a plain
  // iframe/anchor href — fetch it with the token and show the blob instead.
  useEffect(() => {
    if (!doc) return;
    let revoked = false;
    let url: string | null = null;
    setObjectUrl(null);
    setError("");
    api.documentFileUrl(doc.id)
      .then((u) => {
        url = u;
        if (revoked) return URL.revokeObjectURL(u);
        setObjectUrl(u);
      })
      .catch((e) => setError(String(e).replace(/^Error: /, "")));
    return () => {
      revoked = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [doc]);

  const byDocType = useCallback(
    (docType: string | null | undefined) =>
      (docType && documents.find((d) => d.doc_type === docType)) || null,
    [documents],
  );

  const value = useMemo<ViewerContext>(() => ({ open: setDoc, byDocType }), [byDocType]);

  return (
    <DocumentViewerContext.Provider value={value}>
      {children}
      <Dialog open={!!doc} onOpenChange={(o) => !o && setDoc(null)}>
        <DialogContent className="sm:max-w-5xl w-[92vw] h-[88vh] flex flex-col p-4">
          <DialogHeader className="pb-2">
            <DialogTitle className="text-sm font-mono flex flex-wrap items-center gap-3">
              {doc?.filename}
              {doc?.doc_type && (
                <span className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-sans text-xs font-normal text-slate-600">
                  {doc.doc_type}
                </span>
              )}
              {objectUrl && (
                <a href={objectUrl} target="_blank" rel="noreferrer"
                   className="text-xs font-sans font-normal text-blue-700 hover:underline">
                  open in new tab ↗
                </a>
              )}
            </DialogTitle>
          </DialogHeader>
          {error ? (
            <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              Could not load this document: {error}
            </p>
          ) : objectUrl ? (
            <iframe
              src={objectUrl}
              className="flex-1 w-full rounded-md border bg-white"
              title={doc?.filename}
            />
          ) : (
            <p className="flex-1 grid place-items-center text-sm text-slate-500">Loading document…</p>
          )}
        </DialogContent>
      </Dialog>
    </DocumentViewerContext.Provider>
  );
}

/** Inline "see the original document" affordance, for use at any review stage. */
export function SourceDocButton({
  doc,
  label = "View source document",
  missingLabel,
}: {
  doc: ViewableDocument | null;
  label?: string;
  missingLabel?: string;
}) {
  const { open } = useDocumentViewer();

  if (!doc) {
    return missingLabel ? (
      <span className="text-xs text-slate-400">{missingLabel}</span>
    ) : null;
  }

  return (
    <button
      type="button"
      onClick={() => open(doc)}
      title={doc.filename}
      className="inline-flex items-center gap-1 rounded border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-blue-700 transition hover:border-blue-300 hover:bg-blue-50"
    >
      📄 {label}
    </button>
  );
}
