import subprocess
import pytest

@pytest.mark.parametrize("level", ["MAPF00", "MAPF01", "MAPF02", "MAPF03"])
def test_mapf_levels_astar_advanced(level):
    """Test MAPF levels with A* and advanced heuristic"""
    level_file = f"levels/{level}.lvl"
    
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-c", "python3 client.py classic --strategy astar --heuristic advanced",
        "-l", level_file
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=310,
        cwd="/workspaces/mavis_client"
    )
    
    output = result.stdout + result.stderr
    assert "Level solved: Yes" in output, f"Level {level_file} not solved!\n{output}"

