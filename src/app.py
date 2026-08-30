"""
Exercise 01 — Node Registry API

Implement a FastAPI application with the following endpoints:

GET    /health          → health check with DB status
POST   /api/nodes       → register a new node
GET    /api/nodes       → list all nodes
GET    /api/nodes/{name} → get a node by name
PUT    /api/nodes/{name} → update a node
DELETE /api/nodes/{name} → soft-delete a node (set status=inactive)

See README.md for full specification.
"""

# TODO: Implement your FastAPI app here



from typing import List

from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Node
from schemas import HealthResponse, NodeCreate, NodeResponse, NodeUpdate

# Create tables on startup (simple approach; a migrations tool like Alembic
# would be preferred in a larger production system).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Node Registry")


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    nodes_count = db.query(Node).filter(Node.status == "active").count()

    return HealthResponse(status="ok", db=db_status, nodes_count=nodes_count)


@app.post("/api/nodes", response_model=NodeResponse, status_code=201)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    existing = db.query(Node).filter(Node.name == payload.name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Node already exists")

    node = Node(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        status="active",
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@app.get("/api/nodes", response_model=List[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(Node).all()


@app.get("/api/nodes/{name}", response_model=NodeResponse)
def get_node(name: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@app.put("/api/nodes/{name}", response_model=NodeResponse)
def update_node(name: str, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    if payload.host is not None:
        node.host = payload.host
    if payload.port is not None:
        node.port = payload.port

    db.commit()
    db.refresh(node)
    return node


@app.delete("/api/nodes/{name}", status_code=204)
def delete_node(name: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.name == name).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    node.status = "inactive"
    db.commit()
    return Response(status_code=204)
