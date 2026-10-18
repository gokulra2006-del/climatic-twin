from app.core.explainability import explainability_engine
model, fnames = explainability_engine._get_model()
print('Model:', type(model))
print('Fnames length:', len(fnames) if fnames else 0)
