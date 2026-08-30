#!/usr/bin/env node
/**
 * build_report.js — Generator for personal health reports
 *
 * Usage:
 *   node build_report.js <content.json> <output.docx>
 *
 * Reads a JSON content structure and produces a styled Word document.
 * See assets/example_content.json for the full schema.
 *
 * Block types supported:
 *   - "paragraph"       : { text, bold?, italic?, color?, size? }
 *   - "rich_paragraph"  : { runs: [{ text, bold?, italic?, color? }, ...] }
 *   - "subheading"      : { text, color? }
 *   - "bullets"         : { items: ["...", "..."] }  // simple text items
 *   - "rich_bullets"    : { items: [{ runs: [...] }, ...] }
 *   - "numbered"        : { items: ["...", "..."] }
 *   - "info_box"        : { title, paragraphs: ["...", { type, ...}], color }
 *   - "table"           : { headers: [...], rows: [[...], ...] }
 *   - "divider"
 *
 * Colors: blue, green, orange, red, gray
 */

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, PageOrientation, LevelFormat, HeadingLevel,
  BorderStyle, WidthType, ShadingType
} = require('docx');

// ============================================================
// COLOR PALETTE
// ============================================================
const COLORS = {
  blue:        { main: "1F4E79", soft: "DEEBF7" },
  green:       { main: "2E7D32", soft: "E8F5E9" },
  orange:      { main: "E65100", soft: "FFF3E0" },
  red:         { main: "B71C1C", soft: "FFEBEE" },
  gray:        { main: "595959", soft: "F2F2F2" },
  text:        "000000",
  textSoft:    "595959",
  textMuted:   "808080",
  textLight:   "B0B0B0"
};

const colorMain = (name) => (COLORS[name] || COLORS.blue).main;
const colorSoft = (name) => (COLORS[name] || COLORS.blue).soft;

// ============================================================
// PRIMITIVE BUILDERS
// ============================================================

function textRun(opts) {
  const { text, bold, italic, italics, color, size, font } = opts;
  return new TextRun({
    text: text || "",
    bold: !!bold,
    italics: !!(italic || italics),
    color: color || undefined,
    size: size || 22,
    font: font || undefined
  });
}

function paragraph(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.spacingAfter ?? 120, before: opts.spacingBefore },
    alignment: opts.alignment,
    children: [textRun({ text, ...opts })]
  });
}

function richParagraph(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.spacingAfter ?? 120, before: opts.spacingBefore },
    alignment: opts.alignment,
    children: runs.map(r => textRun(r))
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 180 },
    children: [textRun({ text, size: 32, bold: true, color: COLORS.blue.main, font: "Arial" })]
  });
}

function subheading(text, colorName = "blue") {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    children: [textRun({ text, size: 26, bold: true, color: colorMain(colorName), font: "Arial" })]
  });
}

function bullet(text, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 100 },
    children: [textRun({ text })]
  });
}

function richBullet(runs, ref = "bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 100 },
    children: runs.map(r => textRun(r))
  });
}

// ============================================================
// COMPOSITE BUILDERS
// ============================================================

function infoBox(title, contentParagraphs, colorName = "blue") {
  const main = colorMain(colorName);
  const soft = colorSoft(colorName);
  const border = { style: BorderStyle.SINGLE, size: 4, color: main };
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders: { top: border, bottom: border, left: border, right: border },
            width: { size: 9360, type: WidthType.DXA },
            shading: { fill: soft, type: ShadingType.CLEAR },
            margins: { top: 200, bottom: 200, left: 250, right: 250 },
            children: [
              ...(title ? [new Paragraph({
                spacing: { after: 100 },
                children: [textRun({ text: title, size: 24, bold: true, color: main })]
              })] : []),
              ...contentParagraphs
            ]
          })
        ]
      })
    ]
  });
}

function dataTable(headers, rows) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const totalWidth = 9360;
  const colWidth = Math.floor(totalWidth / headers.length);
  const colWidths = headers.map(() => colWidth);
  // Adjust last column to absorb rounding
  colWidths[colWidths.length - 1] = totalWidth - colWidth * (headers.length - 1);

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders,
          width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: COLORS.blue.main, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 120 },
          children: [new Paragraph({
            children: [textRun({ text: h, size: 22, bold: true, color: "FFFFFF" })]
          })]
        }))
      }),
      ...rows.map((row, idx) => new TableRow({
        children: row.map((cell, i) => {
          const cellData = typeof cell === 'string' ? { text: cell } : cell;
          return new TableCell({
            borders,
            width: { size: colWidths[i], type: WidthType.DXA },
            shading: {
              fill: idx % 2 === 0 ? "FFFFFF" : COLORS.gray.soft,
              type: ShadingType.CLEAR
            },
            margins: { top: 80, bottom: 80, left: 120, right: 120 },
            children: [new Paragraph({
              children: [textRun({
                text: cellData.text,
                bold: cellData.bold,
                color: cellData.color
              })]
            })]
          });
        })
      }))
    ]
  });
}

// ============================================================
// BLOCK RENDERER (the heart)
// ============================================================

function renderBlock(block) {
  switch (block.type) {
    case "paragraph":
      return [paragraph(block.text, block)];

    case "rich_paragraph":
      return [richParagraph(block.runs, block)];

    case "subheading":
      return [subheading(block.text, block.color)];

    case "bullets":
      return block.items.map(item => bullet(item));

    case "rich_bullets":
      return block.items.map(item => richBullet(item.runs || item));

    case "numbered":
      return block.items.map(item => bullet(item, "numbers"));

    case "info_box": {
      const innerParagraphs = (block.paragraphs || []).flatMap(p => {
        if (typeof p === 'string') return [paragraph(p)];
        return renderBlock(p);
      });
      return [infoBox(block.title, innerParagraphs, block.color)];
    }

    case "table":
      return [dataTable(block.headers, block.rows)];

    case "divider":
      return [
        new Paragraph({
          spacing: { before: 320, after: 240 },
          alignment: AlignmentType.CENTER,
          children: [textRun({ text: "— — —", color: COLORS.textLight })]
        })
      ];

    default:
      console.warn(`Unknown block type: ${block.type}`);
      return [];
  }
}

function renderSection(section) {
  const children = [];
  if (section.title) {
    children.push(heading1(section.title));
  }
  (section.blocks || []).forEach(b => {
    children.push(...renderBlock(b));
  });
  return children;
}

// ============================================================
// HEADER (cover area)
// ============================================================

function renderHeader(meta) {
  const items = [];
  if (meta.title) {
    items.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
      children: [textRun({
        text: meta.title,
        size: 40, bold: true, color: COLORS.blue.main, font: "Arial"
      })]
    }));
  }
  if (meta.name) {
    items.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
      children: [textRun({ text: meta.name, size: 28, color: COLORS.textSoft })]
    }));
  }
  if (meta.subtitle) {
    items.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 320 },
      children: [textRun({ text: meta.subtitle, size: 22, italic: true, color: COLORS.textMuted })]
    }));
  }
  return items;
}

// ============================================================
// FOOTER (closing note)
// ============================================================

function renderFooter(footer) {
  const items = [
    new Paragraph({
      spacing: { before: 400 },
      alignment: AlignmentType.CENTER,
      children: [textRun({ text: "— — —", color: COLORS.textLight })]
    })
  ];
  (footer.lines || []).forEach((line, idx) => {
    items.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: idx === 0 ? 200 : 0 },
      children: [textRun({ text: line, size: 18, italic: true, color: COLORS.textMuted })]
    }));
  });
  return items;
}

// ============================================================
// MAIN
// ============================================================

function buildDocument(content) {
  const children = [];

  // Cover area
  if (content.meta) {
    children.push(...renderHeader(content.meta));
  }

  // Opening box (special — always at the top, info_box style)
  if (content.opening_box) {
    children.push(...renderBlock({ type: "info_box", ...content.opening_box }));
  }

  // Sections
  (content.sections || []).forEach(s => {
    children.push(...renderSection(s));
  });

  // Footer
  if (content.footer) {
    children.push(...renderFooter(content.footer));
  }

  // Determine font size baseline (slightly larger for elderly)
  const baseFontSize = (content.meta?.large_text) ? 24 : 22;

  return new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: baseFontSize } } },
      paragraphStyles: [
        {
          id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, font: "Arial", color: COLORS.blue.main },
          paragraph: { spacing: { before: 320, after: 180 }, outlineLevel: 0 }
        }
      ]
    },
    numbering: {
      config: [
        {
          reference: "bullets",
          levels: [{
            level: 0, format: LevelFormat.BULLET, text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 540, hanging: 270 } } }
          }]
        },
        {
          reference: "numbers",
          levels: [{
            level: 0, format: LevelFormat.DECIMAL, text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 540, hanging: 270 } } }
          }]
        }
      ]
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, right: 1440, bottom: 1080, left: 1440 }
        }
      },
      children
    }]
  });
}

// CLI entry point
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node build_report.js <content.json> <output.docx>");
    process.exit(1);
  }

  const [contentPath, outputPath] = args;
  const content = JSON.parse(fs.readFileSync(contentPath, 'utf8'));
  const doc = buildDocument(content);

  Packer.toBuffer(doc).then(buffer => {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, buffer);
    console.log(`Report generated: ${outputPath}`);
  }).catch(err => {
    console.error("Failed:", err);
    process.exit(1);
  });
}

module.exports = { buildDocument };
