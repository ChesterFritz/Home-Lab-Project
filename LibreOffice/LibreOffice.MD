# 📄 LibreOffice Headless — Setup Guide

Step-by-step instructions to install and use LibreOffice for document conversion on Armbian Debian Trixie.

---

## Why LibreOffice Headless

LibreOffice is the open source equivalent of Microsoft Office. Running it in headless mode means no GUI — it runs purely as a command line tool for converting documents silently in the background. It's the same engine used by popular self-hosted converters like ConvertX, just without the web UI wrapper.

For a 1GB board, native headless installation is more practical than a Docker container — same result, less overhead.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Hardware | Linux-based SBC or server (tested on Orange Pi PC H3, Armbian Debian Trixie) |
| Access | Root or sudo |
| Disk space | ~300MB for LibreOffice installation |

---

## 1. Install LibreOffice

```bash
sudo apt update
sudo apt install libreoffice -y
```

This installs LibreOffice in headless mode — no desktop or GUI components needed.

---

## 2. Transfer Files to Orange Pi

From your Mac, copy the file you want to convert:

```bash
scp document.docx fritz@192.168.18.28:~/
```

Or use SFTP:

```bash
sftp fritz@192.168.18.28
put document.docx
```

---

## 3. Convert Files

SSH into the Orange Pi first:

```bash
ssh fritz@192.168.18.28
```

Then run the conversion:

### Word to PDF
```bash
libreoffice --headless --convert-to pdf document.docx
```

### PDF to Word
```bash
libreoffice --headless --convert-to docx document.pdf
```

### Excel to PDF
```bash
libreoffice --headless --convert-to pdf spreadsheet.xlsx
```

### PowerPoint to PDF
```bash
libreoffice --headless --convert-to pdf presentation.pptx
```

### Convert to a specific output folder
```bash
libreoffice --headless --convert-to pdf document.docx --outdir ~/output/
```

> **Note:** The converted file will be saved in the same directory as the source file unless `--outdir` is specified.

---

## 4. Transfer Converted File Back to Mac

From your Mac:

```bash
scp fritz@192.168.18.28:~/document.pdf ~/Desktop/
```

---

## 📝 Supported Formats

| Convert From | Convert To |
|-------------|------------|
| `.docx` `.doc` `.odt` | `.pdf` `.docx` `.odt` `.txt` |
| `.xlsx` `.xls` `.ods` | `.pdf` `.xlsx` `.ods` `.csv` |
| `.pptx` `.ppt` `.odp` | `.pdf` `.pptx` `.odp` |
| `.pdf` | `.docx` `.odt` |

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `command not found` | LibreOffice not installed | Run `sudo apt install libreoffice -y` |
| Conversion slow | Normal — H3 is a weak CPU | Wait it out, document conversion is lighter than video |
| Output file missing | Wrong directory | Check with `ls` or use `--outdir` to specify location |
| Formatting looks off | LibreOffice rendering difference | Expected for complex documents — simplify formatting |

---

## 📝 Notes

| Note | Details |
|------|---------|
| Runs natively | No Docker needed — simpler for occasional manual use |
| Disk usage | ~300MB installed |
| RAM usage | Launches, converts, and exits — no persistent RAM usage |
| Formatting | Complex layouts may not convert perfectly — works best with simple documents |

---

## ⏭️ Next Steps

| Guide | Description |
|-------|-------------|
| [Docker Setup](../docker/README.md) | Container runtime |
| [Tailscale Setup](../tailscale/README.md) | Access Orange Pi remotely for file transfers |