# Spatial Flood Inundation & Impact Mapping Methodology (Phase 15)

### Mathematical Formulations

1. **Terrain-Derived Flood Susceptibility ($TSS$)**:
   $$TSS = w_{\text{elev}} \cdot \max(0, 1 - \text{Elev}/25.0) + w_{\text{channel}} \cdot \text{ChannelProximity} + w_{\text{coast}} \cdot \text{CoastProximity} \in [0.0, 1.0]$$

2. **Flood Susceptibility Index ($FSI$)**:
   $$FSI = 0.35 \cdot S_{\text{rain}} + 0.20 \cdot S_{\text{runoff}} + 0.30 \cdot TSS + 0.15 \cdot S_{\text{hist}} \in [0.0, 1.0]$$

3. **Spatial Flood Impact Index ($SFII$)**:
   $$SFII = P(\text{Flood}) \cdot 0.50 + FSI \cdot 0.35 + \text{CompoundBonus} \cdot 0.15 \in [0.0, 1.0]$$

4. **Relative Inundation Severity Classification**:
   - `SEVERE`: $SFII \ge 0.75$
   - `HIGH`: $0.55 \le SFII < 0.75$
   - `MODERATE`: $0.35 \le SFII < 0.55$
   - `LOW`: $SFII < 0.35$
