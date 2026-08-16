import type { City } from "@/types/prediction";

/** Las 15 ciudades admitidas por el modelo (una por provincia incluida). */
export const CITIES: City[] = [
  { id: "babahoyo", name: "Babahoyo", province: "Los Ríos", latitude: -1.8017, longitude: -79.5342 },
  { id: "cuenca", name: "Cuenca", province: "Azuay", latitude: -2.9006, longitude: -79.0045 },
  {
    id: "esmeraldas",
    name: "Esmeraldas",
    province: "Esmeraldas",
    latitude: 0.9682,
    longitude: -79.6517,
  },
  { id: "guayaquil", name: "Guayaquil", province: "Guayas", latitude: -2.1894, longitude: -79.8891 },
  { id: "loja", name: "Loja", province: "Loja", latitude: -3.9931, longitude: -79.2042 },
  {
    id: "macas",
    name: "Macas",
    province: "Morona Santiago",
    latitude: -2.3087,
    longitude: -78.1157,
  },
  { id: "machala", name: "Machala", province: "El Oro", latitude: -3.2586, longitude: -79.9606 },
  {
    id: "nueva-loja",
    name: "Nueva Loja",
    province: "Sucumbíos",
    latitude: 0.0847,
    longitude: -76.8925,
  },
  { id: "portoviejo", name: "Portoviejo", province: "Manabí", latitude: -1.0546, longitude: -80.4545 },
  { id: "puyo", name: "Puyo", province: "Pastaza", latitude: -1.4924, longitude: -77.9962 },
  { id: "quito", name: "Quito", province: "Pichincha", latitude: -0.1807, longitude: -78.4678 },
  { id: "riobamba", name: "Riobamba", province: "Chimborazo", latitude: -1.6636, longitude: -78.6546 },
  { id: "salinas", name: "Salinas", province: "Santa Elena", latitude: -2.2139, longitude: -80.9585 },
  {
    id: "santo-domingo",
    name: "Santo Domingo",
    province: "Santo Domingo de los Tsáchilas",
    latitude: -0.2542,
    longitude: -79.1719,
  },
  { id: "tena", name: "Tena", province: "Napo", latitude: -0.9938, longitude: -77.8129 },
];

export const getCityById = (id: string | null): City | undefined =>
  CITIES.find((c) => c.id === id);

/** Provincias que contienen una ciudad admitida (para resaltado en el mapa). */
export const SELECTABLE_PROVINCES = new Set(CITIES.map((c) => c.province));
