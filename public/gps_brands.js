/**
 * IMED Predictor — Base de Datos de Marcas GPS Deportivas
 * Fuente: Investigación de mercado 2024-2025
 * Cada marca incluye sus column hints específicos que boostean el motor semántico.
 */
const GPS_BRANDS_DB = {

  "statsports": {
    id: "statsports",
    name: "STATSports",
    model: "Apex Series",
    logo: "📡",
    color: "#00B4D8",
    description: "Usado por ligas Premier League, Serie A y selecciones FIFA.",
    region: "Global / Profesional",
    format: "CSV vía SONRA Software",
    metrics: {
      decel_z5:       ["Dec_Above_3m_s2", "High Decels", "HD", "Number of High Decelerations", "Decel (High)", "High Intensity Decelerations"],
      accel_high:     ["Acc_Above_3m_s2", "High Accels", "HA", "Number of High Accelerations", "Accel (High)", "High Intensity Accelerations"],
      max_speed:      ["MaxSpeed", "Max Speed", "Peak Speed", "Max Vel", "Top Speed"],
      distance:       ["TotalDistance", "Total Distance", "Distance (m)", "Dist"],
      sprint_distance:["SprintDistance", "Sprint Distance", "HSR_Distance", "High Speed Running"],
    }
  },

  "catapult": {
    id: "catapult",
    name: "Catapult Sports",
    model: "Vector / OpenField / One",
    logo: "🛰️",
    color: "#FF6B35",
    description: "Estándar en NFL, NHL, AFL y fútbol de élite europeo.",
    region: "Global / Élite",
    format: "CSV vía OpenField Cloud / CTR",
    metrics: {
      decel_z5:       ["Deceleration Total Efforts", "Dcc", "High Deceleration", "High Dec", "Dec Efforts", "Deceleration Efforts >3"],
      accel_high:     ["Acceleration Total Efforts", "Acc", "High Acceleration", "High Acc", "Acc Efforts", "Acceleration Efforts >3"],
      max_speed:      ["Max Velocity", "Max Vel", "Top Speed", "Maximum Speed"],
      distance:       ["Total Distance", "Distance", "Dist (m)"],
      sprint_distance:["Sprint Distance", "HSR Distance", "High Speed Distance"],
    }
  },

  "polar": {
    id: "polar",
    name: "Polar",
    model: "Team Pro",
    logo: "❄️",
    color: "#0066CC",
    description: "Ampliamente usado en clubes amateur y semiprofesionales europeos.",
    region: "Europa / Amateur-Pro",
    format: "CSV vía Polar Team Pro Web",
    metrics: {
      decel_z5:       ["High Deceleration Count", "Decelerations (high)", "Decel High", "Desaceleraciones Altas"],
      accel_high:     ["High Acceleration Count", "Accelerations (high)", "Accel High", "Aceleraciones Altas"],
      max_speed:      ["Maximum Speed", "Max Speed (km/h)", "Velocidad Máxima", "Top Speed"],
      distance:       ["Total Distance (m)", "Distance", "Distancia Total"],
      sprint_distance:["Sprint Distance (m)", "Sprint Dist", "Distancia Sprint"],
    }
  },

  "kinexon": {
    id: "kinexon",
    name: "Kinexon",
    model: "Sports Sensor / Team",
    logo: "🔷",
    color: "#7B2FBE",
    description: "Sistema UWB de alta precisión. Usado en Bundesliga, NBA y Champions.",
    region: "Global / Élite",
    format: "CSV / API JSON vía KINEXON Performance Platform",
    metrics: {
      decel_z5:       ["Deceleration High", "Dec (High)", "Dcc High Intensity", "High Intensity Deceleration"],
      accel_high:     ["Acceleration High", "Acc (High)", "Acc High Intensity", "High Intensity Acceleration"],
      max_speed:      ["Speed Max", "Maximum Speed", "Peak Velocity", "Max Speed"],
      distance:       ["Distance Covered", "Total Distance", "Distanz"],
      sprint_distance:["Sprint Distance", "Speed Zone 4", "HSR"],
    }
  },

  "oliver": {
    id: "oliver",
    name: "Oliver",
    model: "Oliver Performance GPS",
    logo: "⚽",
    color: "#2ECC71",
    description: "Líder en Chile y Latinoamérica. Integración directa con IMED PREDICTOR.",
    region: "Latinoamérica / Chile",
    format: "CSV vía plataforma Oliver",
    metrics: {
      decel_z5:       ["Desaceleraciones Altas", "Dec Alta", "High Decel", "decel_alta", "HighDecels"],
      accel_high:     ["Aceleraciones Altas", "Acel Alta", "High Accel", "accel_alta", "HighAccels"],
      max_speed:      ["Velocidad Máxima", "Vel Max", "Max Speed", "vel_max"],
      distance:       ["Distancia Total", "Distancia (m)", "Distance", "Dist. Recorrida (m)"],
      sprint_distance:["Distancia Sprint", "Sprint", "Sprint Dist"],
    }
  },

  "gpSports": {
    id: "gpSports",
    name: "GPSports",
    model: "SPI Pro / SPI HPU",
    logo: "📍",
    color: "#F39C12",
    description: "Sistema robusto para entornos de alto impacto. Usado en rugby y fútbol australiano.",
    region: "Australia / Global",
    format: "CSV vía SPI ProS Software",
    metrics: {
      decel_z5:       ["Decelerations (high)", "High Deceleration Efforts", "Decel High Band", "Dec_High"],
      accel_high:     ["Accelerations (high)", "High Acceleration Efforts", "Accel High Band", "Acc_High"],
      max_speed:      ["Max Speed", "Peak Speed", "Top Speed (m/s)"],
      distance:       ["Total Distance", "Distance (m)"],
      sprint_distance:["Sprint Distance", "High Speed Running Distance"],
    }
  },

  "garmin": {
    id: "garmin",
    name: "Garmin",
    model: "Instinct / Forerunner Team Edition",
    logo: "🗺️",
    color: "#003087",
    description: "Ecosistema de consumer GPS con datos exportables para análisis de equipo.",
    region: "Global / Consumer-Semi Pro",
    format: "CSV / FIT vía Garmin Connect",
    metrics: {
      decel_z5:       ["Deceleration", "High Intensity Deceleration", "Dec"],
      accel_high:     ["Acceleration", "High Intensity Acceleration", "Acc"],
      max_speed:      ["Max Speed", "Maximum Speed", "Speed (max)", "Velocidad máxima"],
      distance:       ["Distance", "Total Distance", "Distancia"],
      sprint_distance:["Sprint Distance", "High Speed"],
    }
  },

  "playermaker": {
    id: "playermaker",
    name: "Playermaker",
    model: "Boot Sensor",
    logo: "👟",
    color: "#E74C3C",
    description: "Sensor en botín para métricas técnicas. Complementa GPS de chaqueta.",
    region: "Global",
    format: "CSV vía Playermaker Platform",
    metrics: {
      decel_z5:       ["High Deceleration", "Decel High", "Decelerations"],
      accel_high:     ["High Acceleration", "Accel High", "Accelerations"],
      max_speed:      ["Max Speed", "Top Speed", "Max Velocity"],
      distance:       ["Total Distance", "Distance"],
      sprint_distance:["Sprint Distance", "High Speed Distance"],
    }
  },

  "uc_cendia": {
    id: "uc_cendia",
    name: "UC-CENDIA",
    model: "Sistema de Monitoreo UC",
    logo: "🏛️",
    color: "#8B4513",
    description: "Sistema académico desarrollado por la Pontificia Universidad Católica de Chile.",
    region: "Chile",
    format: "CSV personalizado CENDIA",
    metrics: {
      decel_z5:       ["Desaceleraciones Altas", "Dec Alta", "Desacel. Altas", "High Decel"],
      accel_high:     ["Aceleraciones Altas", "Acel Alta", "Acel. Altas", "High Accel"],
      max_speed:      ["Velocidad Máxima", "Vel. Max.", "Max Speed"],
      distance:       ["Distancia Total", "Dist. Total", "Total Distance"],
      sprint_distance:["Distancia Sprint", "Sprint"],
    }
  },

  "auto": {
    id: "auto",
    name: "Detección Automática",
    model: "Motor Semántico IA",
    logo: "🤖",
    color: "#9B59B6",
    description: "El motor de IA analiza el CSV y detecta las columnas automáticamente sin configuración previa.",
    region: "Universal",
    format: "Cualquier CSV",
    metrics: null // Usa solo el motor semántico
  }

};
