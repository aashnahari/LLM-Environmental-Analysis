from dataclasses import dataclass
from schema import Host


@dataclass(frozen=True)
class InfraFactors:
    pue: float          # power usage effectiveness
    wue_site: float      # L/kWh, on-site cooling
    wue_source: float     # L/kWh, off-site power generation
    cif: float     # kg CO2e/kWh, grid carbon intensity


FACTORS = {
    # Azure: Jegham et al. 2025 (arXiv:2505.09598) Table 1, matches Microsoft's
    # own disclosed PUE (<1.12) and WUE (0.30 L/kWh) at datacenters.microsoft.com.
    Host.AZURE: InfraFactors(pue=1.12, wue_site=0.30, wue_source=4.35, cif=0.35),
    # AWS: PUE and CIF/WUE-source from Jegham et al. Table 1. wue_site updated
    # from the paper's 0.18 to AWS's own 2025 Sustainability Report figure
    # (0.12 L/kWh, a 20% YoY improvement) -- more current than the paper's source data.
    Host.AWS:   InfraFactors(pue=1.14, wue_site=0.12, wue_source=5.11, cif=0.287),
}

@dataclass(frozen=True)
class Footprint:
    water_l: float
    carbon_kg: float


def footprint(energy_wh: float, host: Host) -> Footprint:
    """Convert energy (Wh) into water (L) and carbon (kg CO2e) for a given host.
 
        Water (L)   = (Energy_kWh / PUE) * WUE_site  +  Energy_kWh * WUE_source
        Carbon (kg) = Energy_kWh * CIF
    """
    f = FACTORS[host]
    energy_kwh = energy_wh / 1000.0
    water_l = (energy_kwh / f.pue) * f.wue_site + energy_kwh * f.wue_source
    carbon_kg = energy_kwh * f.cif
    return Footprint(water_l=water_l, carbon_kg=carbon_kg)