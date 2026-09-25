import Foundation
import PDFKit

guard CommandLine.arguments.count >= 4 else {
    fputs("usage: extract_pdf_lines.swift <pdf> <start-page> <end-page>\n", stderr)
    exit(2)
}

let path = CommandLine.arguments[1]
let startPage = max(1, Int(CommandLine.arguments[2]) ?? 1)
let requestedEnd = Int(CommandLine.arguments[3]) ?? startPage

guard let document = PDFDocument(url: URL(fileURLWithPath: path)) else {
    fputs("unable to open PDF\n", stderr)
    exit(1)
}

let endPage = min(requestedEnd, document.pageCount)
var pages: [[String: Any]] = []

if startPage <= endPage {
    for pageNumber in startPage...endPage {
        guard let page = document.page(at: pageNumber - 1), let selection = page.selection(for: page.bounds(for: .mediaBox)) else { continue }
        let lines = selection.selectionsByLine().compactMap { line -> [String: Any]? in
            let text = (line.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
            guard !text.isEmpty else { return nil }
            let bounds = line.bounds(for: page)
            return [
                "text": text,
                "x": bounds.origin.x,
                "y": bounds.origin.y,
                "width": bounds.size.width,
                "height": bounds.size.height,
            ]
        }
        pages.append([
            "page": pageNumber,
            "width": page.bounds(for: .mediaBox).width,
            "height": page.bounds(for: .mediaBox).height,
            "lines": lines,
        ])
    }
}

let output = try JSONSerialization.data(withJSONObject: pages, options: [.prettyPrinted, .sortedKeys])
if CommandLine.arguments.count >= 5 {
    try output.write(to: URL(fileURLWithPath: CommandLine.arguments[4]), options: .atomic)
} else {
    FileHandle.standardOutput.write(output)
    FileHandle.standardOutput.write(Data("\n".utf8))
}
