import Foundation
import PDFKit

guard CommandLine.arguments.count == 4 else {
    fputs("usage: extract_pdf_text.swift INPUT.pdf START_PAGE END_PAGE\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let startPage = Int(CommandLine.arguments[2]),
      let endPage = Int(CommandLine.arguments[3]),
      startPage > 0,
      endPage >= startPage,
      let document = PDFDocument(url: inputURL) else {
    fputs("invalid input or page range\n", stderr)
    exit(2)
}

for pageNumber in startPage...min(endPage, document.pageCount) {
    print("\n===== PAGE \(pageNumber) =====")
    print(document.page(at: pageNumber - 1)?.string ?? "")
}
