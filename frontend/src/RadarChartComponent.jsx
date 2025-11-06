import React from 'react';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const RadarChartComponent = ({ uniData }) => {
  if (!uniData) {
    return <div className="text-muted small text-center mt-3">Select a university to see its radar chart.</div>;
  }

  const data = {
    labels: ['Academics', 'Cost', 'Social', 'Accommodation'],
    datasets: [
      {
        label: uniData.uni_name,
        data: [
          uniData.avg_academics || 0,
          uniData.avg_cost || 0,
          uniData.avg_social || 0,
          uniData.avg_accommodation || 0,
        ],
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    scales: {
      r: {
        angleLines: {
          display: true,
        },
        suggestedMin: 0,
        suggestedMax: 5,
        ticks: {
          stepSize: 1,
          color: '#666',
        },
        pointLabels: {
          color: '#333',
          font: {
            size: 14,
          },
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.raw !== null) {
              label += Math.round(context.raw * 100) / 100 + '/5';
            }
            return label;
          },
        },
      },
    },
    responsive: true,
    maintainAspectRatio: false,
  };

  return (
    <div style={{ height: '300px', width: '100%' }}>
      <Radar data={data} options={options} />
    </div>
  );
};

export default RadarChartComponent;
