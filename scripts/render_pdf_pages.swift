import Foundation
import PDFKit
import AppKit

// Renders PDF pages to PNG images for direct visual review (no OCR).
// usage: render_pdf_pages.swift INPUT.pdf START END OUTPUT_DIR [LONG_EDGE_PX]
guard CommandLine.arguments.count >= 5,
      let start = Int(CommandLine.arguments[2]),
      let end = Int(CommandLine.arguments[3]),
      let document = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1])) else {
    fputs("usage: render_pdf_pages.swift INPUT.pdf START END OUTPUT_DIR [LONG_EDGE_PX]\n", stderr)
    exit(2)
}
let outputDirectory = URL(fileURLWithPath: CommandLine.arguments[4], isDirectory: true)
let longEdge = CommandLine.arguments.count >= 6 ? CGFloat(Double(CommandLine.arguments[5]) ?? 1600) : 1600
try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)

for pageNumber in max(1, start)...min(end, document.pageCount) {
    guard let page = document.page(at: pageNumber - 1) else { continue }
    let bounds = page.bounds(for: .cropBox)
    let rotated = page.rotation % 180 != 0
    let pageWidth = rotated ? bounds.height : bounds.width
    let pageHeight = rotated ? bounds.width : bounds.height
    let scale = longEdge / max(pageWidth, pageHeight)
    let width = Int((pageWidth * scale).rounded())
    let height = Int((pageHeight * scale).rounded())
    guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: 0,
                                  space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { continue }
    context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .cropBox, to: context)
    guard let image = context.makeImage() else { continue }
    let rep = NSBitmapImageRep(cgImage: image)
    guard let data = rep.representation(using: .png, properties: [:]) else { continue }
    let url = outputDirectory.appendingPathComponent(String(format: "page-%03d.png", pageNumber))
    try data.write(to: url)
}
