# FinVerify Frontend Integration Audit

Status key: **fixed** | **disabled** | **empty-state**

| Component | Action | Expected behavior | Status |
|-----------|--------|-------------------|--------|
| Sidebar | Navigate | Route changes and page content updates | fixed |
| Header project selector | Change project | Opens selected project workspace | fixed |
| ProjectsPage | New project | Creates real project via API | fixed |
| ProjectsPage | Open project card | Navigates to `/projects/:id` | fixed |
| Project workspace tabs | Click tab | Renders matching child route | fixed |
| UploadPage | Select PDFs / drop files | Calls upload API, refreshes table | fixed |
| CompareTwoDocuments | Select old/new PDF | Stores selection for verification run | fixed |
| VerificationPage | Run Comparison | Calls API with two document IDs | fixed |
| VerificationPage | Result summary | Shows backend verification summary | fixed |
| AnomaliesPage | Load anomalies | Fetches paginated anomalies for active run | fixed |
| AnomaliesTable | View | Opens detail drawer without crash | fixed |
| AnomaliesTable | Pagination | Server page previous/next | fixed |
| ReportsPage | Download Excel/JSON | Real download links or disabled state | fixed |
| DashboardPage | Open projects | Navigates to projects list | fixed |
| Header notifications | Click | Disabled with "Coming soon" | disabled |
| EvidenceViewerPage | View evidence table | Empty state until evidence API is wired per run | empty-state |

Workflow enforced in UI:

1. Create or select project
2. Upload two annual PDFs
3. Select old and new documents
4. Run comparison
5. Review anomalies
6. Download reports
