import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

export default function TechniqueChart({ breakdown }) {
  // Filter out techniques with 0 count
  const data = breakdown.filter(item => item.count > 0);

  if (data.length === 0) {
    return null;
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-900 border border-gray-700 p-3 rounded-lg shadow-xl text-sm">
          <p className="font-semibold text-white mb-1" style={{ color: data.color }}>{data.technique}</p>
          <p className="text-gray-300">Occurrences: {data.count}</p>
          <p className="text-gray-400">Avg Conf: {data.avg_confidence}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-panel p-8 rounded-2xl">
      <h3 className="text-sm font-semibold text-gray-300 mb-6 uppercase tracking-widest text-center">Technique Breakdown</h3>
      
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={70}
              paddingAngle={2}
              dataKey="count"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-col gap-2">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
              <span className="text-gray-300">{item.technique}</span>
            </div>
            <span className="text-gray-500 bg-gray-800 px-2 rounded-md">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
