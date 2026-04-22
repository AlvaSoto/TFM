# Makefile para TFM: Backend (FastAPI) y Frontend (React + Vite)

.PHONY: help backend frontend install-backend install-frontend run-backend run-frontend clean-backend clean-frontend clean-all

help:
	@echo "Comandos disponibles:"
	@echo "  make install-backend   # Instala dependencias del backend (requiere entorno Python activado)"
	@echo "  make install-frontend  # Instala dependencias del frontend (Node.js 22.12.0 y npm)"
	@echo "  make run-backend       # Ejecuta el backend con Uvicorn (requiere entorno Python activado)"
	@echo "  make run-frontend      # Ejecuta el frontend (Vite)"
	@echo "  make clean-backend     # Elimina __pycache__ y archivos temporales del backend"
	@echo "  make clean-frontend    # Elimina node_modules y dist del frontend"
	@echo "  make clean-all         # Limpia backend y frontend"

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

run-backend:
	cd backend && uvicorn app.api.router:app --reload

run-frontend:
	cd frontend && npm run dev

clean-backend:
	find backend -type d -name '__pycache__' -exec rm -rf {} +
	find backend -type f -name '*.pyc' -delete

clean-frontend:
	rm -rf frontend/node_modules frontend/dist frontend/package-lock.json

clean-all: clean-backend clean-frontend
