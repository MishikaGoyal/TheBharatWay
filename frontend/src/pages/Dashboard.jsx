import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';

function Dashboard() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const fetchUserData = async () => {
    try {
      const res = await axios.get('http://localhost:5000/api/auth/dashboard', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      setUser(res.data.user);
    } catch (err) {
      alert('Unauthorized or session expired');
      navigate('/login');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  return (
    <div className="max-w-xl mx-auto mt-10">
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      {user ? (
        <>
          <p className="mb-4">Welcome, {user.email}</p>
          <button
            onClick={handleLogout}
            className="bg-red-500 text-white px-4 py-2 rounded"
          >
            Logout
          </button>
        </>
      ) : (
        <p>Loading user data...</p>
      )}
    </div>
  );
}

export default Dashboard;