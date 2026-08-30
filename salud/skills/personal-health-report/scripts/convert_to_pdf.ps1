# Convierte un .docx a .pdf usando Microsoft Word por COM (Windows).
# Uso: powershell -File convert_to_pdf.ps1 -DocxPath "C:\ruta\informe.docx" [-PdfPath "C:\ruta\informe.pdf"]
# Si no se pasa -PdfPath, genera el PDF junto al .docx con el mismo nombre.
param(
    [Parameter(Mandatory = $true)][string]$DocxPath,
    [string]$PdfPath
)

$DocxPath = (Resolve-Path $DocxPath).Path
if (-not $PdfPath) {
    $PdfPath = [System.IO.Path]::ChangeExtension($DocxPath, ".pdf")
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    # Open(FileName, ConfirmConversions, ReadOnly)
    $doc = $word.Documents.Open($DocxPath, $false, $true)
    # 17 = wdExportFormatPDF
    $doc.ExportAsFixedFormat($PdfPath, 17)
    $doc.Close($false)
    Write-Output "PDF generado: $PdfPath"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
