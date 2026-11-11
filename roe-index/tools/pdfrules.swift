// Prints horizontal table rules of every page as JSON: {"p": page, "y": from page top, "x0", "x1"}.
// Tracks the CTM (cm, q, Q) and collects thin filled rectangles (re) and stroked lines (m/l).
import Foundation
import CoreGraphics

struct M { var a=1.0,b=0.0,c=0.0,d=1.0,e=0.0,f=0.0
  func apply(_ x: Double,_ y: Double)->(Double,Double){(a*x+c*y+e, b*x+d*y+f)}
  func concat(_ m: M)->M { // self' = m * self
    M(a: m.a*a+m.b*c, b: m.a*b+m.b*d, c: m.c*a+m.d*c, d: m.c*b+m.d*d, e: m.e*a+m.f*c+e, f: m.e*b+m.f*d+f) } }
final class St { var ctm = M(); var stack: [M] = []; var nums: [Double] = []; var cur: (Double,Double)? = nil
  var segs: [(Double,Double,Double,Double)] = [] }
var st = St()
func pop(_ s: CGPDFScannerRef, _ n: Int) -> [Double]? {
  var out: [Double] = []
  for _ in 0..<n { var v: CGPDFReal = 0; guard CGPDFScannerPopNumber(s, &v) else { return nil }; out.insert(Double(v), at: 0) }
  return out }
let table = CGPDFOperatorTableCreate()!
CGPDFOperatorTableSetCallback(table, "q") { _, _ in st.stack.append(st.ctm) }
CGPDFOperatorTableSetCallback(table, "Q") { _, _ in if let m = st.stack.popLast() { st.ctm = m } }
CGPDFOperatorTableSetCallback(table, "cm") { s, _ in guard let v = pop(s, 6) else { return }
  st.ctm = st.ctm.concat(M(a: v[0], b: v[1], c: v[2], d: v[3], e: v[4], f: v[5])) }
CGPDFOperatorTableSetCallback(table, "re") { s, _ in guard let v = pop(s, 4) else { return }
  let p0 = st.ctm.apply(v[0], v[1]), p1 = st.ctm.apply(v[0]+v[2], v[1]+v[3])
  let w = abs(p1.0-p0.0), h = abs(p1.1-p0.1)
  if h < 2.5 && w > 5 { st.segs.append((min(p0.0,p1.0), max(p0.0,p1.0), (p0.1+p1.1)/2, 0)) }
  else if w > 5 && h > 5 { // a cell rectangle: its top and bottom are rules
    st.segs.append((min(p0.0,p1.0), max(p0.0,p1.0), min(p0.1,p1.1), 0)); st.segs.append((min(p0.0,p1.0), max(p0.0,p1.0), max(p0.1,p1.1), 0)) } }
CGPDFOperatorTableSetCallback(table, "m") { s, _ in guard let v = pop(s, 2) else { return }; st.cur = st.ctm.apply(v[0], v[1]) }
CGPDFOperatorTableSetCallback(table, "l") { s, _ in guard let v = pop(s, 2) else { return }
  let p = st.ctm.apply(v[0], v[1]); if let c = st.cur, abs(c.1-p.1) < 1, abs(c.0-p.0) > 5 { st.segs.append((min(c.0,p.0), max(c.0,p.0), p.1, 0)) }; st.cur = p }
let doc = CGPDFDocument(URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL)!
var out: [[String: Any]] = []
for i in 1...doc.numberOfPages {
  let page = doc.page(at: i)!; let box = page.getBoxRect(.mediaBox)
  st = St()
  let cs = CGPDFContentStreamCreateWithPage(page); let sc = CGPDFScannerCreate(cs, table, nil); CGPDFScannerScan(sc)
  for s in st.segs { out.append(["p": i, "y": Int((box.maxY - s.2).rounded()), "x0": Int(s.0 - box.minX), "x1": Int(s.1 - box.minX)]) }
}
FileManager.default.createFile(atPath: CommandLine.arguments[2], contents: try! JSONSerialization.data(withJSONObject: out))
print("rules:", out.count)
