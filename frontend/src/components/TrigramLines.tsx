const SIZES = { sm: { w: 52, h: 7, gap: 4 }, lg: { w: 132, h: 14, gap: 8 } };

export function TrigramLines({ lines, size = "sm" }: { lines: number[]; size?: "sm" | "lg" }) {
  const s = SIZES[size];
  const rows = [...lines].reverse(); // рисуем сверху вниз
  return (
    <div className="trigram-lines" style={{ width: s.w }}>
      {rows.map((bit, i) => (
        <div
          className="tl-row"
          key={i}
          style={{ height: s.h, marginBottom: i < rows.length - 1 ? s.gap : 0 }}
        >
          {bit === 1 ? (
            <span className="tl-bar" style={{ width: "100%" }} />
          ) : (
            <>
              <span className="tl-bar" style={{ width: "43%" }} />
              <span className="tl-bar" style={{ width: "43%" }} />
            </>
          )}
        </div>
      ))}
    </div>
  );
}
