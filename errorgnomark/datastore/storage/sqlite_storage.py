# errorgnomark/datastore/storage/sqlite_storage.py

"""
SQLite implementation of the BaseStorage interface.

This module provides a concrete storage backend that saves experimental data
to a local SQLite database file. It uses SQLAlchemy for ORM capabilities.
"""

# -------------------------------------------------------------------
# 1. Standard Library Imports
# -------------------------------------------------------------------
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

# -------------------------------------------------------------------
# 2. Third-Party Imports
# -------------------------------------------------------------------
from sqlalchemy import create_engine, Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Use for type hint, but will be string in SQLite

# -------------------------------------------------------------------
# 3. Internal Framework Imports
# -------------------------------------------------------------------
from .base import BaseStorage
from ..models import ExperimentRun, RBParameters, RBResultData

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ==============================================================================
# SQLAlchemy Database Schema Definition
# ==============================================================================

# Base class for our ORM models
Base = declarative_base()

class ExperimentRunDB(Base):
    """SQLAlchemy ORM model corresponding to the ExperimentRun Pydantic model."""
    __tablename__ = "experiment_runs"

    # Columns
    id = Column(String, primary_key=True, index=True)
    workflow_run_id = Column(String, index=True, nullable=True)
    protocol_name = Column(String, index=True)
    backend_name = Column(String, index=True)
    creation_timestamp = Column(DateTime)
    tags = Column(JSON)
    parameters = Column(JSON)
    results = Column(JSON)
    shots = Column(Integer)

# ==============================================================================
# SQLite Storage Implementation
# ==============================================================================

class SQLiteStorage(BaseStorage):
    """
    Stores experiment data in a SQLite database.
    """
    def __init__(self, db_path: str = "errorgnomark_data.db"):
        """
        Initializes the SQLite storage backend.

        Args:
            db_path: The file path for the SQLite database.
        """
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None

    def connect(self) -> None:
        """Creates the database engine and tables if they don't exist."""
        if self.engine is None:
            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logging.info(f"Connected to SQLite database at: {self.db_path}")

    def close(self) -> None:
        """Closes the engine connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            logging.info("Disconnected from SQLite database.")

    def _get_db_session(self) -> Session:
        if not self.SessionLocal:
            raise ConnectionError("Database is not connected. Call connect() first.")
        return self.SessionLocal()

    def save_run(self, run_data: ExperimentRun) -> ExperimentRun:
        """Saves a single ExperimentRun to the SQLite database."""
        db = self._get_db_session()
        try:
            # Convert Pydantic model to a dictionary suitable for the DB model
            db_run_dict = run_data.dict()
            # SQLAlchemy's JSON type handles dicts, but UUIDs need to be strings
            db_run_dict['id'] = str(run_data.id)
            if run_data.workflow_run_id:
                db_run_dict['workflow_run_id'] = str(run_data.workflow_run_id)
            
            db_run = ExperimentRunDB(**db_run_dict)
            
            db.add(db_run)
            db.commit()
            db.refresh(db_run)
            
            # Return a new Pydantic model from the committed data
            return ExperimentRun.from_orm(db_run)
        finally:
            db.close()

    def get_run_by_id(self, run_id: UUID) -> Optional[ExperimentRun]:
        """Retrieves a run by its UUID."""
        db = self._get_db_session()
        try:
            db_run = db.query(ExperimentRunDB).filter(ExperimentRunDB.id == str(run_id)).first()
            if db_run:
                return ExperimentRun.from_orm(db_run)
            return None
        finally:
            db.close()

    def find_runs(self, query_filters: Optional[Dict[str, Any]] = None) -> List[ExperimentRun]:
        """Finds runs matching filters."""
        db = self._get_db_session()
        try:
            query = db.query(ExperimentRunDB)
            if query_filters:
                # This is a simplified filter. A real implementation would handle
                # nested keys in 'tags' or value ranges.
                for key, value in query_filters.items():
                    if hasattr(ExperimentRunDB, key):
                        query = query.filter(getattr(ExperimentRunDB, key) == value)
            
            db_runs = query.all()
            return [ExperimentRun.from_orm(run) for run in db_runs]
        finally:
            db.close()

# ==============================================================================
# Example Usage
# ==============================================================================
if __name__ == '__main__':
    # This demonstrates how to use the SQLiteStorage class.
    
    # 1. Create a storage instance
    storage = SQLiteStorage(db_path="test_storage.db")

    # Use a context manager to handle connect/close
    with storage:
        # 2. Create some fake RB result data (as would be produced by the API)
        rb_params = RBParameters(
            qubits=[0],
            depths=[1, 10, 20, 50],
            circuits_per_depth=10,
            seed=1234
        )
        rb_results = RBResultData(
            fit_successful=True,
            alpha=0.999,
            epc=7.5e-4,
            raw_survival_probabilities=[0.98, 0.9, 0.8, 0.5],
            raw_std_errors=[0.01, 0.02, 0.03, 0.05]
        )

        # 3. Create the main ExperimentRun object
        my_run = ExperimentRun(
            protocol_name="StandardRB",
            backend_name="ideal_qpu_3q",
            tags={"user": "demo", "calibration_version": "v1.2"},
            parameters=rb_params,
            results=rb_results,
            shots=1024
        )
        
        print(f"Attempting to save run: {my_run.id}")
        
        # 4. Save the run
        saved_run = storage.save_run(my_run)
        print("Run saved successfully.")
        print(f"Saved run details: {saved_run}")

        # 5. Retrieve the run by its ID
        retrieved_run = storage.get_run_by_id(saved_run.id)
        print(f"\nRetrieved run by ID: {retrieved_run.id}")
        assert retrieved_run.id == saved_run.id
        assert retrieved_run.results.epc == 7.5e-4
        print("Data retrieval verified.")

        # 6. Find runs using a filter
        found_runs = storage.find_runs(query_filters={"backend_name": "ideal_qpu_3q"})
        print(f"\nFound {len(found_runs)} runs for backend 'ideal_qpu_3q'.")
        assert len(found_runs) > 0
        print("Filter query verified.")