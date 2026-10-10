from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class PredictionModel(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    version = Column(String, nullable=False)
    type = Column(String, nullable=True) # e.g., 'ML', 'Physical', 'Statistical'
    description = Column(String, nullable=True)
    
    predictions = relationship("ModelPrediction", back_populates="model")
    evaluations = relationship("ModelEvaluation", back_populates="model")

class ModelPrediction(Base):
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("infrastructure_assets.id"), nullable=True)
    prediction_time = Column(DateTime(timezone=True), nullable=False, index=True)
    forecast_horizon = Column(Integer, nullable=True) # Hours ahead
    predicted_value = Column(Float, nullable=True)
    probability = Column(Float, nullable=True)
    uncertainty_info = Column(JSON, nullable=True)
    
    model = relationship("PredictionModel", back_populates="predictions")
    asset = relationship("InfrastructureAsset", back_populates="predictions")

class ModelEvaluation(Base):
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    evaluation_time = Column(DateTime(timezone=True), nullable=False, index=True)
    metrics = Column(JSON, nullable=False) # e.g., {'RMSE': 0.5, 'MAE': 0.3}
    
    model = relationship("PredictionModel", back_populates="evaluations")
