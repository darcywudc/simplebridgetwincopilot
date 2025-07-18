import logging
from bridge_model_enhanced import BridgeModelXara

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_analysis.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Test the core logic of the Streamlit application"""
    logging.info("Starting application logic test")

    # 1. Create the bridge model with default parameters
    bridge = BridgeModelXara()
    logging.info("Bridge model created")

    # 2. Apply a point load
    point_load = -100000  # -100 kN
    point_position = 0.5
    bridge.add_point_load(point_load, point_position)
    logging.info(f"Applied point load: {point_load / 1000} kN at position {point_position}")

    # 3. Run the analysis
    results = bridge.run_analysis()
    logging.info("Analysis completed")

    # 4. Check the results
    if results['analysis_ok']:
        logging.info("Analysis was successful")
        max_disp = results['max_displacement']
        max_moment = results['max_moment']
        max_shear = results['max_shear']
        reactions = results['reactions']

        logging.info(f"Max displacement: {max_disp * 1000:.2f} mm")
        logging.info(f"Max moment: {max_moment / 1000:.2f} kN*m")
        logging.info(f"Max shear: {max_shear / 1000:.2f} kN")
        logging.info(f"Reactions: {reactions}")

        # Basic sanity checks
        assert max_disp < 0, "Max displacement should be negative (downwards)"
        assert len(reactions) == bridge.num_piers, "Number of reactions should match number of piers"

        # Check if the sum of reactions equals the applied load
        total_reaction = sum(r['Fy'] for r in reactions)
        applied_load = point_load
        # Self-weight
        self_weight = bridge.density * 9.81 * bridge.A * bridge.length
        applied_load -= self_weight

        # Allow for a small tolerance
        assert abs(total_reaction + applied_load) < 1e-3, f"Sum of reactions ({total_reaction:.2f}) does not equal applied load ({-applied_load:.2f})"

        # Check for reasonable moment and shear values
        assert abs(max_moment) > 0, "Max moment should be non-zero"
        assert abs(max_shear) > 0, "Max shear should be non-zero"
    else:
        logging.error("Analysis failed")
        logging.error(f"Error: {results['error']}")

if __name__ == "__main__":
    main()
