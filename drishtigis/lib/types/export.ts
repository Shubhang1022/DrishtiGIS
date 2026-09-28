export interface ExportFormatInfo {
  id: string;
  name: string;
  extension: string;
  status: string;
}

export interface ExportLayerInfo {
  id: string;
  name: string;
  source: string;
}

export interface ExportCRSInfo {
  crs: string;
  name: string;
  type: string;
}

export interface ExportFormatsResponse {
  supported_formats: ExportFormatInfo[];
  supported_layers: ExportLayerInfo[];
  supported_crss: ExportCRSInfo[];
  _disclaimer: string;
}

export interface ExportRequestPayload {
  dataset_id?: string;
  region_id?: string;
  layers: string[];
  output_format: string;
  output_crs: string;
  city?: string;
  state?: string;
  country?: string;
}
