#!/usr/bin/env bash
# Quick-start script for Investment Promotion Agency GTD environment
# This script sets up a complete DevOps AI environment for investment tracking

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_prereqs=()

    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_prereqs+=("Docker")
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        missing_prereqs+=("Docker Compose")
    fi

    # Check Ollama
    if ! command -v ollama &> /dev/null; then
        log_warning "Ollama not found. Install from: https://ollama.com/download"
        log_info "You can continue without Ollama, but AI features will be limited."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    if [ ${#missing_prereqs[@]} -ne 0 ]; then
        log_error "Missing prerequisites: ${missing_prereqs[*]}"
        log_info "Please install missing tools and try again."
        exit 1
    fi

    log_success "All prerequisites met!"
}

# Setup environment file
setup_env_file() {
    log_info "Setting up environment configuration..."

    if [ -f "$DOCKER_DIR/.env" ]; then
        log_warning ".env file already exists"
        read -p "Overwrite with investment agency template? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing .env file"
            return
        fi
    fi

    # Copy investment agency template
    if [ -f "$DOCKER_DIR/.env.investment-agency.example" ]; then
        cp "$DOCKER_DIR/.env.investment-agency.example" "$DOCKER_DIR/.env"
        log_success "Created .env from investment agency template"
    elif [ -f "$DOCKER_DIR/.env.example" ]; then
        cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
        log_success "Created .env from standard template"
    else
        log_error "No .env template found!"
        exit 1
    fi

    # Prompt for key values
    log_info "Please configure key settings:"

    read -p "Site name (default: invest.localhost): " site_name
    site_name=${site_name:-invest.localhost}
    sed -i.bak "s/SITE_NAME=.*/SITE_NAME=$site_name/" "$DOCKER_DIR/.env"
    sed -i.bak "s/FRAPPE_SITE=.*/FRAPPE_SITE=$site_name/" "$DOCKER_DIR/.env"

    read -sp "Admin password (leave empty to auto-generate): " admin_pass
    echo
    if [ -z "$admin_pass" ]; then
        admin_pass=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-16)
        log_info "Generated admin password: $admin_pass"
        log_warning "SAVE THIS PASSWORD! You'll need it to log in."
    fi
    sed -i.bak "s/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$admin_pass/" "$DOCKER_DIR/.env"

    # Enable Ollama if available
    if command -v ollama &> /dev/null; then
        sed -i.bak "s/ENABLE_OLLAMA=.*/ENABLE_OLLAMA=1/" "$DOCKER_DIR/.env"
        log_success "Enabled Ollama AI integration"
    fi

    # Clean up backup files
    rm -f "$DOCKER_DIR/.env.bak"

    log_success "Environment configuration complete!"
}

# Pull and setup Ollama models
setup_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_warning "Ollama not installed, skipping model setup"
        return
    fi

    log_info "Setting up Ollama AI models..."

    # Check if Ollama service is running
    if ! ollama list &> /dev/null; then
        log_warning "Ollama service not running. Starting it..."
        # Try to start Ollama in background
        if command -v systemctl &> /dev/null; then
            sudo systemctl start ollama || true
        else
            log_info "Please start Ollama manually in another terminal: ollama serve"
            read -p "Press Enter when Ollama is running..."
        fi
    fi

    # Pull recommended models
    log_info "Pulling llama3.2:3b (lightweight, recommended)..."
    ollama pull llama3.2:3b || log_warning "Failed to pull llama3.2:3b"

    log_info "Pulling llama3.1:8b (higher quality, optional)..."
    read -p "This is a larger model (~5GB). Download? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull llama3.1:8b || log_warning "Failed to pull llama3.1:8b"
    fi

    log_success "Ollama setup complete!"
}

# Pull Docker images
pull_images() {
    log_info "Pulling Docker images (this may take a while)..."

    cd "$DOCKER_DIR"

    if [ -f "run.sh" ]; then
        bash run.sh prefetch
        log_success "Docker images pulled and saved for offline use"
    else
        docker compose pull
        log_success "Docker images pulled"
    fi
}

# Start services
start_services() {
    log_info "Starting services..."

    cd "$DOCKER_DIR"

    if [ -f "run.sh" ]; then
        bash run.sh up
    else
        docker compose up -d
    fi

    log_success "Services started!"
}

# Initialize Frappe site
initialize_site() {
    log_info "Initializing Frappe site (this will take 5-10 minutes)..."

    cd "$DOCKER_DIR"

    # Wait for services to be healthy
    log_info "Waiting for database to be ready..."
    sleep 10

    if [ -f "run.sh" ]; then
        bash run.sh init
    else
        docker compose exec backend bench new-site "$site_name" \
            --admin-password "$admin_pass" \
            --install-app erpnext
    fi

    log_success "Site initialized!"
}

# Create sample GTD data
create_sample_data() {
    log_info "Creating sample GTD opportunities and projects..."

    cd "$DOCKER_DIR"

    # This would call a Python script to create sample data
    # For now, just log the intent
    log_info "Sample data creation would happen here"
    log_info "You can manually create opportunities via the web interface"
}

# Display completion message
show_completion() {
    log_success "════════════════════════════════════════════════════════════"
    log_success "  Investment Promotion Agency AI Environment Ready!  "
    log_success "════════════════════════════════════════════════════════════"
    echo ""
    log_info "Access your system:"
    log_info "  • ERPNext Desk: http://localhost:8000"
    log_info "  • AI Gateway: http://localhost:8001"
    log_info "  • API Docs: http://localhost:8001/docs"
    echo ""
    log_info "Login credentials:"
    log_info "  • Username: Administrator"
    log_info "  • Password: (the password you set above)"
    echo ""
    log_info "Next steps:"
    log_info "  1. Log in to ERPNext Desk"
    log_info "  2. Create your first Investment Opportunity"
    log_info "  3. Try the GTD Capture AI assistant"
    log_info "  4. Review the documentation: docs/DEVOPS_AI_GTD_SETUP.md"
    echo ""
    log_info "Useful commands:"
    log_info "  • View logs: cd infra/docker && bash run.sh logs"
    log_info "  • Stop services: cd infra/docker && bash run.sh down"
    log_info "  • Backup data: cd infra/docker && bash run.sh backup"
    echo ""
    log_success "Happy investing! 🚀"
    log_success "════════════════════════════════════════════════════════════"
}

# Main setup flow
main() {
    echo ""
    log_info "════════════════════════════════════════════════════════════"
    log_info "  Investment Promotion Agency - DevOps AI Setup  "
    log_info "════════════════════════════════════════════════════════════"
    echo ""

    check_prerequisites
    setup_env_file
    setup_ollama

    log_info "Ready to pull images and start services"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Setup cancelled. You can run this script again anytime."
        exit 0
    fi

    pull_images
    start_services

    log_info "Ready to initialize Frappe site"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Services are running but site not initialized."
        log_info "Run: cd infra/docker && bash run.sh init"
        exit 0
    fi

    initialize_site

    # Optional: Create sample data
    read -p "Create sample GTD opportunities for testing? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_sample_data
    fi

    show_completion
}

# Run main setup
main "$@"
