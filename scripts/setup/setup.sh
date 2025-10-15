#!/bin/bash

#######################################################
# EPL Match Predictor - Automated Setup Script
# Version: 2.0
# Description: One-click setup for new development environment
#######################################################

set -e  # Exit on error

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Progress bar function
print_header() {
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

# Banner
clear
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███████╗██████╗ ██╗         ██████╗ ██████╗  ███████╗  ║
║   ██╔════╝██╔══██╗██║         ██╔══██╗██╔══██╗ ██╔════╝  ║
║   █████╗  ██████╔╝██║         ██████╔╝██████╔╝ █████╗    ║
║   ██╔══╝  ██╔═══╝ ██║         ██╔═══╝ ██╔══██╗ ██╔══╝    ║
║   ███████╗██║     ███████╗    ██║     ██║  ██║ ███████╗  ║
║   ╚══════╝╚═╝     ╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚══════╝  ║
║                                                           ║
║         EPL Match Predictor v2.0 - Setup Wizard          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_info "Player Analysis-Based AI Prediction Platform"
echo ""
sleep 1

# Check if running on macOS
print_header "1/8 System Check"
print_step "Checking operating system..."
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_warning "This script is optimized for macOS"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "macOS detected"
fi

# Check for Homebrew
print_step "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found"
    print_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    print_success "Homebrew installed"
else
    print_success "Homebrew found: $(brew --version | head -n 1)"
fi

# Check for Python
print_header "2/8 Python Check"
print_step "Checking for Python 3.9+..."
if ! command -v python3 &> /dev/null; then
    print_warning "Python not found"
    print_info "Installing Python 3.9..."
    brew install python@3.9
    print_success "Python installed"
else
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    print_success "Python found: $PYTHON_VERSION"

    # Check if version is 3.9+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d '.' -f 1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d '.' -f 2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_warning "Python 3.9+ required (current: $PYTHON_VERSION)"
        print_info "Installing Python 3.9..."
        brew install python@3.9
    fi
fi

# Check for Node.js
print_header "3/8 Node.js Check"
print_step "Checking for Node.js 18+..."
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found"
    print_info "Installing Node.js..."
    brew install node
    print_success "Node.js installed"
else
    NODE_VERSION=$(node --version | cut -d 'v' -f 2)
    print_success "Node.js found: v$NODE_VERSION"

    # Check if version is 18+
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d '.' -f 1)

    if [ "$NODE_MAJOR" -lt 18 ]; then
        print_warning "Node.js 18+ required (current: v$NODE_VERSION)"
        print_info "Updating Node.js..."
        brew upgrade node
    fi
fi

# Backend setup
print_header "4/8 Backend Setup"
print_step "Setting up Python virtual environment..."
cd backend

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing..."
    rm -rf venv
fi

python3 -m venv venv
print_success "Virtual environment created"

print_step "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

print_step "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"

print_step "Installing Python dependencies..."
print_info "This may take a few minutes..."
pip install -r requirements.txt --quiet
print_success "Python dependencies installed"

# Environment variables setup
print_header "5/8 Environment Variables"
print_step "Checking for .env file..."
if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success ".env file created from template"
    else
        print_info "Keeping existing .env file"
    fi
else
    cp .env.example .env
    print_success ".env file created from template"
fi

print_warning "⚠️  IMPORTANT: Edit backend/.env with your API keys!"
print_info "Required keys:"
echo "  - CLAUDE_API_KEY (from https://console.anthropic.com/)"
echo "  - ODDS_API_KEY (from https://the-odds-api.com/)"
echo "  - SECRET_KEY (generate with: openssl rand -hex 32)"
echo ""

read -p "Do you want to open .env file now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v code &> /dev/null; then
        code .env
    elif command -v nano &> /dev/null; then
        nano .env
    else
        open .env
    fi
fi

# Database initialization
print_header "6/8 Database Initialization"
print_step "Checking for database..."
if [ -f "epl_predictor.db" ]; then
    print_info "Database already exists"
    read -p "Reinitialize database? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm epl_predictor.db
        print_step "Initializing database..."
        python init_database.py
        print_success "Database initialized"
    else
        print_info "Using existing database"
    fi
else
    print_step "Initializing database..."
    if [ -f "init_database.py" ]; then
        python init_database.py
        print_success "Database initialized"
    else
        print_info "No database initialization script found (optional)"
    fi
fi

deactivate
cd ..

# Frontend setup
print_header "7/8 Frontend Setup"
print_step "Installing Node.js dependencies..."
cd frontend/epl-predictor

if [ -d "node_modules" ]; then
    print_warning "node_modules already exists. Removing..."
    rm -rf node_modules
fi

print_info "This may take a few minutes..."
npm install --silent

if [ $? -eq 0 ]; then
    print_success "Node.js dependencies installed"
else
    print_error "Failed to install Node.js dependencies"
    exit 1
fi

cd ../..

# Create start script
print_header "8/8 Creating Start Script"
print_step "Creating start.sh..."

cat > start.sh << 'STARTSCRIPT'
#!/bin/bash

# EPL Match Predictor - Quick Start Script
# Starts both backend and frontend concurrently

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}Starting EPL Match Predictor...${NC}"
echo ""

# Trap Ctrl+C to kill both processes
trap 'kill $(jobs -p)' EXIT

# Start backend
echo -e "${BLUE}[Backend]${NC} Starting Flask API on port 5001..."
cd backend
source venv/bin/activate
python api/app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}[Frontend]${NC} Starting React app on port 3000..."
cd frontend/epl-predictor
npm start &
FRONTEND_PID=$!
cd ../..

echo ""
echo -e "${GREEN}✅ Both services started!${NC}"
echo ""
echo -e "${PURPLE}Access the application:${NC}"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:5001"
echo ""
echo -e "${PURPLE}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
STARTSCRIPT

chmod +x start.sh
print_success "start.sh created"

# Completion
print_header "Setup Complete! 🎉"
echo ""
print_success "EPL Match Predictor v2.0 is ready to use!"
echo ""
print_info "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Run: ./start.sh"
echo "  3. Open: http://localhost:3000"
echo ""
print_warning "Don't forget to set up your API keys in backend/.env!"
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}       Happy predicting! ⚽ Built with Claude Code${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Ask if user wants to start now
read -p "Do you want to start the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting application..."
    ./start.sh
else
    print_info "Run './start.sh' when you're ready to start"
fi
