"""
tests/test_milp_allocator.py — Tests for Group Rooming & Fleet Allocation Solvers.
"""

from src.logistics.milp_allocator import (
    FleetAllocationSolver,
    GroupRoomingAllocator,
    TravelerRoomingProfile,
)


def test_group_rooming_allocator_couples_and_singles():
    """Verify room allocator pairs couples in double rooms and isolates singles."""
    travelers = [
        TravelerRoomingProfile(traveler_id="t1", name="Alice", gender="female", couple_partner_id="t2"),
        TravelerRoomingProfile(traveler_id="t2", name="Bob", gender="male", couple_partner_id="t1"),
        TravelerRoomingProfile(traveler_id="t3", name="Charlie", gender="male", requires_single_room=True),
        TravelerRoomingProfile(traveler_id="t4", name="David", gender="male"),
        TravelerRoomingProfile(traveler_id="t5", name="Eve", gender="male"),
    ]

    res = GroupRoomingAllocator.allocate_rooms(travelers, room_rate_per_night_usd=200.0, single_supplement_pct=0.50)
    assert res.total_travelers == 5
    assert res.double_rooms_count == 1
    assert res.twin_rooms_count == 1
    assert res.single_rooms_count == 1
    assert res.total_rooms == 3
    assert res.total_cost_usd > 0


def test_fleet_allocation_solver_family_and_large_group():
    """Verify fleet allocator selects single SUV for 5 pax and Motorcoach for large group."""
    small = FleetAllocationSolver.solve_fleet(passengers_count=5, luggage_pieces_count=6)
    assert "Luxury SUV / Minivan" in small.allocated_vehicles
    assert small.allocated_vehicles["Luxury SUV / Minivan"] == 1

    large = FleetAllocationSolver.solve_fleet(passengers_count=35, luggage_pieces_count=40)
    assert "Luxury Motorcoach" in large.allocated_vehicles
    assert large.allocated_vehicles["Luxury Motorcoach"] == 1
