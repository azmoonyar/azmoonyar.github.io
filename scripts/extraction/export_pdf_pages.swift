import Foundation
import PDFKit

guard CommandLine.arguments.count == 5 else {
    fputs("usage: export_pdf_pages.swift INPUT.pdf START_PAGE END_PAGE OUTPUT_DIR\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let startPage = Int(CommandLine.arguments[2]),
      let endPage = Int(CommandLine.arguments[3]),
      startPage > 0,
      endPage >= startPage,
      let source = PDFDocument(url: inputURL) else {
    fputs("invalid input or page range\n", stderr)
    exit(2)
}

let outputDirectory = URL(fileURLWithPath: CommandLine.arguments[4], isDirectory: true)
try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)

for pageNumber in startPage...min(endPage, source.pageCount) {
    guard let page = source.page(at: pageNumber - 1) else { continue }
    let output = PDFDocument()
    output.insert(page, at: 0)
    let fileName = String(format: "page-%02d.pdf", pageNumber)
    let outputURL = outputDirectory.appendingPathComponent(fileName)
    guard output.write(to: outputURL) else {
        fputs("failed to write page \(pageNumber)\n", stderr)
        exit(1)
    }
}
