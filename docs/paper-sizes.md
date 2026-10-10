# Designed paper sizes per BIR form template

Survey of the 84 form templates embedded in the eBIRForms Offline Package **v7.9.6.2**
(`BIRForms.exe` RT_HTML resource bundle). For each form, evidence was collected from:
`@page` CSS rules, print-path warning alerts (bound to the Print button where possible),
fixed per-page `Print*Content` div geometry, and BIR's own `img/for_printing` reference
scans.

Designed sizes: **legal 8.5x13 in** (27),
**unknown / no declaration** (45), **A4** (6),
**mixed (A4-declared, legal-laid-out)** (5),
**legal 8.5x14 in** (1).

The 45 *unknown* forms declare nothing anywhere: in the original app their paper size was
decided by Internet Explorer / printer defaults at print time, which is why scale-to-fit is
the only robust strategy for A4 export.

| Form | Designed paper | Confidence | Evidence |
|---|---|---|---|
| 0605 | unknown | low | print clamp max-width:8.3in |
| 0619E | A4 | medium | alert[printOCR]=A4: "printed on A4 Size Paper. Please update your Printer Settings (Set Paper Size to A4 under Preferences -> Advan..."; BIR scans 0619-E-Pg1.png=1700x2200(letter 8.5x11); barcode folder 0619E_BarCode |
| 0619F | A4 | medium | alert[printOCR]=A4: "printed on A4 Size Paper. Please update your Printer Settings (Set Paper Size to A4 under Preferences -> Advan..."; BIR scans 0619-F-Pg1.png=1700x2200(letter 8.5x11); barcode folder 0619F_BarCode |
| 0620 | unknown | low | print clamp max-width:8.3in; barcode folder 0620_BarCode |
| 1600 | unknown | low | print clamp max-width:8.3in |
| 1600PTv2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1600PTv2018_BarCode |
| 1600VTv2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1600VTv2018_BarCode |
| 1600WP | unknown | low | print clamp max-width:8.3in |
| 1601C | unknown | low | print clamp max-width:8.3in |
| 1601Cv2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1601C_BarCode |
| 1601E | unknown | low | print clamp max-width:8.3in |
| 1601EQ | A4 | medium | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1601EQ_BarCode |
| 1601F | unknown | low | print clamp max-width:8.3in |
| 1601FQ | A4 | medium | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1601FQ_BarCode |
| 1602 | unknown | low | print clamp max-width:8.3in |
| 1602Qv2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; print clamp max-width:8.3in; barcode folder 1602Q_BarCode |
| 1603 | unknown | low | print clamp max-width:8.3in |
| 1603Qv2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1603Q_BarCode |
| 1604C | unknown | low | print clamp max-width:8.3in; barcode folder 1604C_BarCode |
| 1604CF | unknown | low | print clamp max-width:8.3in |
| 1604E | unknown | low | print clamp max-width:8.3in |
| 1604Ev2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1604Ev2018_BarCode |
| 1604F | unknown | low | print clamp max-width:8.3in; barcode folder 1604F_BarCode |
| 1606 | unknown | low | print clamp max-width:8.3in |
| 1621 | unknown | low | print clamp max-width:8.3in; barcode folder 1621_BarCode |
| 1700 | unknown/mixed | low | @page size:8.26in 11.69in; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printOCR]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; containers container 8.5x13in, formPaper 8.26x11.69in, wrapper 8.26x11.69in; PrintNContent divs 850x1280px x4 pages; BIR scans BIRForm_1700_0.png=850x1300(legal 8.5x13); BIRForm_1700_1.png=850x1300(legal 8.5x13); BIRForm_1700_2.png=850x1300(legal 8.5x13) +1 more; print clamp max-width:8.3in; barcode folder 1700_BarCode |
| 1700v2018 | A4 | high | alert[printNow]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1700v2018_BarCode |
| 1701 | unknown/mixed | low | @page size:8.26in 11.69in; alert[printOCR]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; containers formPaper 8.26x11.69in, wrapper 8.26x11.69in; PrintNContent divs 826x1250px x12 pages; BIR scans 82255BIR Form 1701 Attachment1.png=850x1300(legal 8.5x13); 82255BIR Form 1701 Attachment2.png=850x1300(legal 8.5x13); 82255BIR Form 1701 Attachment3.png=850x1300(legal 8.5x13) +14 more; print clamp max-width:8.3in; barcode folder 1701_BarCode |
| 1701A | unknown | low | print clamp max-width:8.3in; barcode folder 1701A_BarCode |
| 1701MS | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. If you are going to save this to a file, saving as PDF or XPS is allowed."); //..."; barcode folder 1701MS_BarCode |
| 1701Q | unknown | low | print clamp max-width:8.3in |
| 1701Qv2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1701Q_BarCode |
| 1701v2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. If you are going to save this to a file, saving as PDF or XPS is allowed."); } ..."; print clamp max-width:8.3in; barcode folder 1701v2018_BarCode |
| 1702EX | unknown/mixed | low | @page width:8.27in height:11.69in; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; containers formPaper 8.27x11.69in, wrapper 8.3x11.69in; PrintNContent divs 850x1300px x14 pages; BIR scans BIR Form 1702-EX1.png=2550x3900(legal 8.5x13); BIR Form 1702-EX2.png=2550x3900(legal 8.5x13); BIR Form 1702-EX3.png=2550x3900(legal 8.5x13) +4 more; print clamp max-width:8.3in; barcode folder 1702EX_BarCode |
| 1702EXv2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1702EXv2018V2_BarCode |
| 1702EXv2018C | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1702EXv2018V2_BarCode |
| 1702MX | unknown/mixed | low | @page size:8.26in 11.69in; alert[printOCR]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; containers formPaper 8.26x11.69in, wrapper 8.26x11.69in; PrintNContent divs 826x1250px x9 pages; BIR scans 1702MX Mandatory Attachments1.png=850x1300(legal 8.5x13); 1702MX Mandatory Attachments2.png=850x1300(legal 8.5x13); 1702MX Mandatory Attachments3.png=850x1300(legal 8.5x13) +10 more; print clamp max-width:8.3in; barcode folder 1702MX_BarCode |
| 1702MXv2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1702MXv2018_BarCode |
| 1702MXv2018C | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1702MXv2018_BarCode |
| 1702MXv2018Cxx | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1702MXv2018_BarCode |
| 1702Q | unknown | low | print clamp max-width:8.3in |
| 1702Qv2008C | unknown | low | print clamp max-width:8.3in |
| 1702Qv2018C | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. If you are going to save this to a file, saving as PDF or XPS is allowed."); //..."; print clamp max-width:8.3in; barcode folder 1702v2018_BarCode |
| 1702RT | unknown/mixed | low | @page size:8.26in 11.69in; alert[printme]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; containers wrapper 8.26x11.69in; PrintNContent divs 846x1280px x8 pages; BIR scans 82314BIR Form 1702-RT1.png=850x1300(legal 8.5x13); 82314BIR Form 1702-RT2.png=850x1300(legal 8.5x13); 82314BIR Form 1702-RT3.png=850x1300(legal 8.5x13) +5 more; print clamp max-width:8.3in; barcode folder 1702RT_BarCode |
| 1702RTv2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1702RTv2018_BarCode |
| 1702RTv2018C | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; print clamp max-width:8.3in; barcode folder 1702RTv2018_BarCode |
| 1704 | unknown | low | print clamp max-width:8.3in |
| 1706 | unknown | low | print clamp max-width:8.3in |
| 1707 | unknown | low | print clamp max-width:8.3in |
| 1707A | legal 8.5x13 | medium | @page width:8.5in height:13in; alert[printModal]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; containers formPaper 8.5x13in, wrapper 8.5x13in; PrintNContent divs 850x1300px; BIR scans BIR Form 1707A_1.png=1704x2504(odd(r=0.681)) |
| 1707Av2021 | legal 8.5x13 | high | @page width:8.5in height:13in; alert[printModal]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; alert[printme]=legal 8.5x13: "printed on a Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form...."; containers formPaper 8.5x13in, wrapper 8.5x13in; PrintNContent divs 850x1300px; print clamp max-width:8.3in; barcode folder 1707Av2021_BarCode |
| 1707v2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1707v2018_BarCode |
| 1707v2021 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 1707v2018_BarCode,1707v2021_BarCode |
| 1800 | unknown | low | print clamp max-width:8.3in |
| 1800v2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1800v2018_BarCode |
| 1801 | unknown | low | print clamp max-width:8.3in |
| 1801v2018 | unknown | low | print clamp max-width:8.3in; barcode folder 1801v2018_BarCode |
| 2000 | unknown | low | print clamp max-width:8.3in |
| 2000OT | unknown | low | print clamp max-width:8.3in |
| 2000OTv2018 | unknown | low | print clamp max-width:8.3in; barcode folder 2000OTv2018_BarCode |
| 2000v2018 | unknown | low | print clamp max-width:8.3in; barcode folder 2000_BarCode |
| 2200A | legal 8.5x13 | high | @page size:8.5in 13in; alert[printOCR]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; alert[printModal]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; containers formPaper 8.5x13in, wrapper 8.5x13in; BIR scans 2200-A-Pg1.png=1700x2600(legal 8.5x13); 2200-A-Pg2.png=1700x2600(legal 8.5x13); print clamp max-width:8.3in |
| 2200AN | unknown | low | print clamp max-width:8.3in |
| 2200ANv2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; print clamp max-width:8.3in; barcode folder 2200ANv2018_BarCode |
| 2200Av2020 | legal 8.5x13 | medium | BIR scans 2200-A-Pg1.png=1700x2600(legal 8.5x13); 2200-A-Pg2.png=1700x2600(legal 8.5x13); print clamp max-width:8.3in; barcode folder 2200Av2020_BarCode |
| 2200Cv2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 2200Cv2018_BarCode |
| 2200M | unknown | low | print clamp max-width:8.3in |
| 2200Mv2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 2200Mv2018_BarCode |
| 2200P | unknown | low | print clamp max-width:8.3in |
| 2200Pv2020 | legal 8.5x14 | high | @page width:8.5in height:14in; alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; containers formPaper 8.5x14in, wrapper 8.5x14in; print clamp max-width:8.3in; barcode folder 2200Pv2020_BarCode |
| 2200S | legal 8.5x13 | high | @page size:8.5in 13in; alert[printOCR]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; alert[printModal]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; containers formPaper 8.5x13in, wrapper 8.5x13in; BIR scans 2200-S-Pg1.png=1700x2600(legal 8.5x13); 2200-S-Pg2.png=1700x2600(legal 8.5x13); print clamp max-width:8.3in; barcode folder 2200S_BarCode |
| 2200T | legal 8.5x13 | high | @page size:8.5in 13in; size:landscape; size:8.5in 13in; alert[printOCR]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; alert[printModal]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; containers formPaper 8.5x13in, wrapper 8.5x13in; BIR scans 2200-T-Pg1.png=1700x2600(legal 8.5x13); 2200-T-Pg2.png=1700x2600(legal 8.5x13); print clamp max-width:8.3in |
| 2200Tv2020 | legal 8.5x13 | medium | BIR scans 2200-T-Pg1.png=1700x2600(legal 8.5x13); 2200-T-Pg2.png=1700x2600(legal 8.5x13); print clamp max-width:8.3in; barcode folder 2200Tv2020_BarCode |
| 2550DS | unknown | low | barcode folder 2550DS_BarCode |
| 2550DS-old | unknown | low | barcode folder 2550DS_BarCode |
| 2550M | unknown | low | print clamp max-width:8.3in |
| 2550Q | unknown | low | print clamp max-width:8.3in |
| 2550Qv2024 | A4 | high | @page size:A4 portrait; barcode folder 2550Qv2024_BarCode |
| 2551 | unknown | low | print clamp max-width:8.3in |
| 2551M | unknown | low | print clamp max-width:8.3in |
| 2551Qv2018 | legal 8.5x13 | high | alert[printme]=legal 8.5x13: "printed on Legal Size Paper. Please update your Printer Settings (Set Paper Size to Legal under Preferences ->..."; print clamp max-width:8.3in; barcode folder 2551Qv2018_BarCode |
| 2552 | unknown | low | print clamp max-width:8.3in |
| 2552v2018 | legal 8.5x13 | high | alert[printModal]=A4: "printed on an A4 Size Paper. Please update your Printer Settings to ensure the correct printout of the form.\n..."; alert[printme]=legal 8.5x13: "printed on an Legal Size Paper. Please update your Printer Settings to ensure the correct printout of the form..."; print clamp max-width:8.3in; barcode folder 2552v2018_BarCode |
| 2553 | unknown | low | print clamp max-width:8.3in |
