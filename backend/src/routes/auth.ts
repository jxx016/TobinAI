import { Router, Request, Response, NextFunction } from 'express';
import { supabase, prisma } from '../index';
import { AppError } from '../middleware/errorHandler';
import { z } from 'zod';

const router = Router();

// Validation schemas
const signupSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2),
  role: z.enum(['TENANT', 'LANDLORD', 'SERVICE_PROVIDER']),
  phoneNumber: z.string().optional(),
});

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

// Signup endpoint
router.post('/signup', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { email, password, name, role, phoneNumber } = signupSchema.parse(req.body);

    // Create user in Supabase Auth
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (authError) throw new AppError(400, authError.message);

    if (!authData.user) throw new AppError(400, 'Failed to create user');

    // Create user in our database
    const user = await prisma.user.create({
      data: {
        id: authData.user.id,
        email,
        name,
        role,
        phoneNumber,
        authId: authData.user.id,
      },
    });

    res.status(201).json({
      status: 'success',
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
        },
      },
    });
  } catch (error) {
    next(error);
  }
});

// Login endpoint
router.post('/login', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { email, password } = loginSchema.parse(req.body);

    // Sign in with Supabase
    const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) throw new AppError(401, 'Invalid credentials');

    if (!authData.user) throw new AppError(401, 'User not found');

    // Get user from our database
    const user = await prisma.user.findUnique({
      where: { authId: authData.user.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        phoneNumber: true,
      },
    });

    if (!user) throw new AppError(404, 'User not found in database');

    res.json({
      status: 'success',
      data: {
        user,
        session: authData.session,
      },
    });
  } catch (error) {
    next(error);
  }
});

// Logout endpoint
router.post('/logout', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw new AppError(400, error.message);

    res.json({
      status: 'success',
      message: 'Logged out successfully',
    });
  } catch (error) {
    next(error);
  }
});

// Get current user
router.get('/me', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { data: { user: authUser }, error: authError } = await supabase.auth.getUser();
    
    if (authError) throw new AppError(401, 'Not authenticated');
    if (!authUser) throw new AppError(404, 'User not found');

    const user = await prisma.user.findUnique({
      where: { authId: authUser.id },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        phoneNumber: true,
      },
    });

    if (!user) throw new AppError(404, 'User not found in database');

    res.json({
      status: 'success',
      data: { user },
    });
  } catch (error) {
    next(error);
  }
});

export const authRouter = router; 