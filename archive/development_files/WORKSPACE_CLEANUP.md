# Workspace Cleanup Script

This directory contains temporary development and testing files that can be safely archived or removed after Features 01 & 02 completion.

## 🗂️ **Files to Archive/Remove**

### **Temporary Test Files**
- `debug_test.py` - Debug testing during development
- `simple_test.py` - Basic integration testing  
- `quick_feature_test.py` - Quick feature validation
- `test_backend_simple.py` - Backend testing
- `test_feature_02.py` - Feature 02 testing
- `test_fixes.py` - Bug fix validation
- `test_integration.py` - Integration testing
- `test_system.py` - System-wide testing
- `verify_imports.py` - Import verification
- `working_test.py` - Development testing

### **Temporary Launch Scripts**
- `launch_system.sh` - System launch script
- `launch_fixed.sh` - Fixed launch script
- `quick_start_backend.py` - Quick backend startup
- `run_backend.py` - Backend runner
- `start_backend.py` - Backend starter

### **Development Files**
- `feature_02_completion_report.py` - Report generator script
- `setup.py.backup` - Backup of old setup file

## 🧹 **Cleanup Actions**

### **Keep (Production Files)**
- `README.md` - Main project documentation
- `FEATURE_01_COMPLETION_REPORT.md` - Feature 01 documentation
- `FEATURE_02_COMPLETION_REPORT.md` - Feature 02 documentation
- `pyproject.toml` - Python project configuration
- `.env` - Environment variables
- `bond_stress_scheduler.py` - Production scheduler
- `csv_signal_tracker.py` - Production CSV tracker
- `backend/` - Production backend code
- `recession_tracker/` - Production frontend code
- `docs/` - Project documentation

### **Archive (Development Files)**
```bash
# Create archive directory
mkdir -p archive/development_files

# Move test files
mv debug_test.py archive/development_files/
mv simple_test.py archive/development_files/
mv quick_feature_test.py archive/development_files/
mv test_*.py archive/development_files/
mv verify_imports.py archive/development_files/
mv working_test.py archive/development_files/

# Move temporary scripts
mv launch_*.sh archive/development_files/
mv quick_start_backend.py archive/development_files/
mv run_backend.py archive/development_files/
mv start_backend.py archive/development_files/
mv feature_02_completion_report.py archive/development_files/

# Move backup files
mv setup.py.backup archive/development_files/
```

## 📁 **Final Clean Project Structure**

```
AI_Chip_Trading_Signals/
├── README.md                          # 📖 Main project documentation
├── FEATURE_01_COMPLETION_REPORT.md    # ✅ Bond monitoring completion
├── FEATURE_02_COMPLETION_REPORT.md    # ✅ Signal generation completion
├── .env                               # 🔑 Environment configuration
├── pyproject.toml                     # 🐍 Python dependencies
├── bond_stress_scheduler.py           # 🕒 Production scheduler
├── csv_signal_tracker.py             # 📊 CSV tracking utility
│
├── backend/                           # 🔧 Production backend
│   ├── src/main.py                    # FastAPI server
│   ├── src/data_sources/              # Data clients
│   ├── src/signals/                   # Signal engines
│   ├── src/models/                    # ML models
│   ├── src/utils/                     # Utilities
│   └── data/trading_signals.db       # Database
│
├── recession_tracker/                 # 🖥️ Production frontend
│   ├── src/app/                       # Next.js app
│   ├── src/components/                # React components
│   └── src/lib/                       # API utilities
│
├── docs/                              # 📚 Documentation
│   ├── features/                      # Feature specifications
│   └── stories/                       # User stories
│
└── archive/                           # 🗄️ Development artifacts
    └── development_files/             # Archived test files
```

This cleanup maintains all production code while archiving development artifacts for future reference.
