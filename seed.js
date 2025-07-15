const mongoose = require('mongoose');
const Employee = require('./models/Employee');
const dotenv = require('dotenv');

dotenv.config();

const seedDatabase = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/hr-assistant');
    console.log('MongoDB connected for seeding.');

    // Clear existing employees (optional, for clean testing)
    // await Employee.deleteMany({});
    // console.log('Existing employees cleared.');

    // Create a test employee
    const testEmployee = new Employee({
      firstName: 'Test',
      lastName: 'Employee',
      email: 'test.employee@example.com',
      password: 'password123',
      department: 'IT',
      position: 'Developer',
      hireDate: new Date(),
      status: 'active',
      leaveBalance: {
        casual: 15,
        sick: 10,
        annual: 20
      },
      role: 'employee'
    });

    const createdEmployee = await testEmployee.save();
    console.log('Test employee created with ID:', createdEmployee._id);

    mongoose.connection.close();
    console.log('MongoDB connection closed.');
  } catch (error) {
    console.error('Error seeding database:', error);
    mongoose.connection.close();
  }
};

seedDatabase(); 