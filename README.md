# Student Placement Management System

Desktop application (Python + Tkinter/ttk) for managing students, companies, jobs,
eligibility, applications and placement status. Data is stored in local JSON files.
No external packages are needed.

## Project structure

```
StudentPlacementSystem/
├── main.py            Entry point: window, sidebar, page switching, admin login
├── config.py          Colours, fonts, statuses, admin password, data folder
├── utils.py           Validation + helper functions (ValidationError)
├── database.py        Collection (one JSON file) and Database (all rules/relations)
├── graphics.py        Anti-aliased rounded shapes, line icons and the logo (drawn in code)
├── widgets.py         Theme, buttons, inputs, dialogs, Card, Form, DataTable, CrudPage base
├── dashboard.py       Dashboard page
├── students.py        Student management page
├── companies.py       Company management page
├── jobs.py            Job management page
├── eligibility.py     Eligibility rules + Eligibility Checker page
├── applications.py    Applications, history, status updates
├── requirements.txt   (no external packages)
├── tests/test_logic.py  Unit tests (no GUI needed)
├── sample_data/       Optional demo data (copy into data/ to try the app)
└── data/              Created automatically on first run
    ├── students.json
    ├── companies.json
    ├── jobs.json
    └── applications.json
```

How the pieces connect: `main.py` creates one `Database` and passes it to every page.
`students.py`, `companies.py` and `jobs.py` all extend `CrudPage` in `widgets.py`, so
each only describes its own form fields, table columns and database calls.

Relationships: `applications.student_id -> students.id`, `applications.job_id -> jobs.id`,
`jobs.company_id -> companies.id`. Deleting a student, job or company also deletes the
records that depend on it (you are asked to confirm first).

## Run on Windows

1. Install Python 3.9+ from https://www.python.org/downloads/ (tick **Add python.exe to PATH**;
   keep the default "tcl/tk and IDLE" option ticked).
2. Open Command Prompt in the project folder:
   ```
   cd path\to\StudentPlacementSystem
   python main.py
   ```
3. Optional demo data: copy the four files from `sample_data\` into a `data\` folder
   next to `main.py` (create it if needed) **before** starting the app.
4. Run the unit tests (optional): `python -m unittest discover tests -v`

## Look and feel

* Sharp on every screen: the app declares itself DPI-aware on Windows and scales all sizes,
  so text and controls are crisp on 125% / 150% / 200% displays (no blurry upscaling).
* Custom-drawn rounded buttons with hover/pressed states, a sidebar with icons, an icon
  logo, soft card shadows, striped borderless tables with thin scrollbars, progress bars on
  the dashboard and themed pop-up dialogs instead of the plain Windows message boxes.
* All colours live in `config.py` (navy, white, emerald green) - change them in one place.

## Rules you should know

* **Eligibility:** CGPA >= the job's minimum CGPA **and** the student has every required
  skill (case-insensitive). Students who are not eligible cannot apply; the reason is shown.
* **Admin:** changing/deleting application status needs the placement-officer password
  (default `admin123`, change `ADMIN_PASSWORD` in `config.py`). Use the sidebar button
  to log in/out. Adding students/jobs and applying does not need the password.
* **Selected status** requires a joining date (YYYY-MM-DD, not before the application date).
* **Placed students** on the dashboard = students with at least one *Selected* application.
* Package is stored in LPA (lakhs per annum).
* A damaged/invalid JSON file is renamed `*.corrupt` and replaced by an empty file; a
  warning is shown at startup. Empty or missing files are created automatically.

## Feature testing checklist

**Startup / storage**
- [ ] First run creates `data/` with the four JSON files.
- [ ] Empty a JSON file, restart: app opens normally.
- [ ] Put `{bad` in `students.json`, restart: warning shown, `.corrupt` backup created.
- [ ] Close and reopen the app: all data is still there.

**Students**
- [ ] Add a valid student; it appears in the table and in `students.json`.
- [ ] Same roll number again (also in different case) is rejected.
- [ ] Invalid CGPA (11, abc), email, phone, empty skills, name with digits are rejected.
- [ ] Search by name and by roll number; searching for nonsense shows "No students found".
- [ ] Click a row, edit, Update: table and JSON change. Delete asks for confirmation.
- [ ] Deleting a student with applications also removes those applications.

**Companies & jobs**
- [ ] Add companies; duplicate company name rejected; invalid website rejected.
- [ ] Jobs page lists the companies in the drop-down; add a job with min CGPA, package, link.
- [ ] Duplicate role at the same company rejected.
- [ ] Search jobs by company name and by role; edit and delete a job.
- [ ] "Open Application Link" opens the browser; a job without a link shows a message.
- [ ] Deleting a company removes its jobs and applications.

**Eligibility**
- [ ] A student with enough CGPA and all skills shows green **ELIGIBLE**.
- [ ] Low CGPA shows **NOT ELIGIBLE** with the CGPA reason.
- [ ] Missing skills are listed by name.
- [ ] Changing a job's minimum CGPA changes the result.
- [ ] "Check All Jobs for Student" fills the table (green = eligible, red = not).

**Applications**
- [ ] Apply with an eligible student; status is Applied, today's date is stored.
- [ ] Applying to the same job twice is rejected; an ineligible student is rejected.
- [ ] After applying, you are offered to open the application link.
- [ ] Update Status asks for the admin password; a wrong password is refused.
- [ ] Selected without a joining date (or an invalid date) is rejected.
- [ ] Filter by status; search by student, roll number, company, role.
- [ ] "Student History" shows all applications of the selected student.

**Dashboard**
- [ ] Counts for students, companies, applications and placed students are correct.
- [ ] Mark an application Selected: Placed count and status breakdown update.
- [ ] Quick Navigation buttons open the right pages.

**Window**
- [ ] Resize and maximise; tables and forms stay usable.
- [ ] Text and icons look sharp (not blurry) on a high-DPI Windows display.
- [ ] Success / warning / error / confirm pop-ups appear as styled dialogs.

## Build a Windows executable (PyInstaller)

```
pip install pyinstaller
cd path\to\StudentPlacementSystem
pyinstaller --noconfirm --onefile --windowed --name PlacementSystem main.py
```

The program is created at `dist\PlacementSystem.exe`. It creates its own `data\` folder
next to the `.exe`, so copy the `.exe` to a folder where you have write permission
(for example `C:\PlacementSystem\`). To keep existing data, copy your `data\` folder
there too. Delete the `build\` folder and `PlacementSystem.spec` afterwards if you like.
