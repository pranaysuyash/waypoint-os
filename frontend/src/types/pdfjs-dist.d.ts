declare module 'pdfjs-dist/build/pdf.mjs' {
  export const GlobalWorkerOptions: {
    workerSrc: string;
  };

  export interface PDFTextItem {
    str?: string;
  }

  export interface PDFPageTextContent {
    items: PDFTextItem[];
  }

  export interface PDFPageProxy {
    getTextContent(): Promise<PDFPageTextContent>;
  }

  export interface PDFDocumentProxy {
    numPages: number;
    getPage(pageNumber: number): Promise<PDFPageProxy>;
  }

  export function getDocument(input: {
    data: ArrayBuffer | Uint8Array;
  }): {
    promise: Promise<PDFDocumentProxy>;
  };
}
