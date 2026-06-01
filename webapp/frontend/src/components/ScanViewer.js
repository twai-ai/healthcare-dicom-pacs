import React from 'react';
import { Image as ImageIcon, BarChart2 } from 'lucide-react';

/**
 * Displays chest X-ray / DICOM preview and optional histogram.
 */
function ScanViewer({ imageStatistics, title = 'Chest X-Ray Scan', compact = false }) {
  if (!imageStatistics) {
    return (
      <div className="scan-viewer scan-viewer--empty">
        <ImageIcon size={40} color="var(--gray-400)" />
        <p>No scan image available for this patient.</p>
        <p className="scan-viewer-hint">
          Run sync_study_images or upload a DICOM file to generate previews.
        </p>
      </div>
    );
  }

  const {
    main_image_data,
    histogram_image_data,
    windowed_image_data,
    mean_intensity,
    std_intensity,
    min_intensity,
    max_intensity,
    snr,
  } = imageStatistics;

  if (!main_image_data && !histogram_image_data && !windowed_image_data) {
    return (
      <div className="scan-viewer scan-viewer--empty">
        <ImageIcon size={40} color="var(--gray-400)" />
        <p>Scan data exists but preview images are not loaded yet.</p>
      </div>
    );
  }

  return (
    <div className={`scan-viewer ${compact ? 'scan-viewer--compact' : ''}`}>
      <div className="scan-viewer-main">
        {main_image_data && (
          <figure className="scan-figure">
            <figcaption>{title}</figcaption>
            <img src={main_image_data} alt={title} className="scan-image scan-image--primary" />
          </figure>
        )}
        {windowed_image_data && !compact && (
          <figure className="scan-figure">
            <figcaption>Windowed view</figcaption>
            <img src={windowed_image_data} alt="Windowed DICOM" className="scan-image" />
          </figure>
        )}
      </div>
      {!compact && histogram_image_data && (
        <div className="scan-viewer-side">
          <h3>
            <BarChart2 size={18} />
            Pixel intensity
          </h3>
          <img src={histogram_image_data} alt="Intensity histogram" className="scan-image scan-image--histogram" />
          <div className="scan-stats">
            {mean_intensity != null && <span>Mean: {mean_intensity.toFixed(1)}</span>}
            {std_intensity != null && <span>Std: {std_intensity.toFixed(1)}</span>}
            {min_intensity != null && max_intensity != null && (
              <span>
                Range: {min_intensity.toFixed(0)} – {max_intensity.toFixed(0)}
              </span>
            )}
            {snr != null && <span>SNR: {snr.toFixed(2)}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

export default ScanViewer;
