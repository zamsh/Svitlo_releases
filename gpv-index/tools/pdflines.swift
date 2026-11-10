// Prints every text line of a PDF as JSON: {"p": page, "x": left, "y": top (from page top), "w": width, "t": text}.
import PDFKit
let doc = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!
var out: [[String: Any]] = []
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i), let sel = page.selection(for: page.bounds(for: .mediaBox)) else { continue }
    let h = page.bounds(for: .mediaBox).height
    for line in sel.selectionsByLine() {
        guard let t = line.string?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty else { continue }
        let b = line.bounds(for: page)
        out.append(["p": i + 1, "x": Int(b.minX), "y": Int(h - b.maxY), "w": Int(b.width), "t": t])
    }
}
let data = try! JSONSerialization.data(withJSONObject: out)
FileManager.default.createFile(atPath: CommandLine.arguments[2], contents: data)
print("lines:", out.count)
