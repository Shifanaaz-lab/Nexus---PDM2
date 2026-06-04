import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect } from "react";
import { Lock, Shield, Activity, Zap, Eye, EyeOff, AlertCircle, CheckCircle2, XCircle } from "lucide-react";
import { useNavigate } from "react-router";
import { CinematicBackground } from "./CinematicBackground";
import { audioSystem } from "./AudioSystem";

const MAX_LOGIN_ATTEMPTS = 3;
const LOCKOUT_TIME = 30000; // 30 seconds
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours

interface ValidationError {
  field: string;
  message: string;
}

export function LoginScreen() {
  const navigate = useNavigate();

  // Load saved credentials on mount
  const savedUser = localStorage.getItem("rememberedUser");
  const savedCredentials = savedUser ? JSON.parse(savedUser) : null;

  const [operatorId, setOperatorId] = useState(savedCredentials?.operatorId || "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [isLockedOut, setIsLockedOut] = useState(false);
  const [lockoutTimer, setLockoutTimer] = useState(0);
  const [touched, setTouched] = useState({ operatorId: false, password: false });
  const [rememberMe, setRememberMe] = useState(!!savedCredentials);
  const [autoLoginChecked, setAutoLoginChecked] = useState(false);

  // Password strength indicators
  const [passwordStrength, setPasswordStrength] = useState({
    hasMinLength: false,
    hasUpperCase: false,
    hasLowerCase: false,
    hasNumber: false,
    hasSpecialChar: false,
  });

  // Check for existing session (disabled auto-login to ensure full flow: login -> bootscreen -> dashboard)
  useEffect(() => {
    setAutoLoginChecked(true);
  }, []);

  const validateOperatorId = (id: string): string | null => {
    if (!id.trim()) {
      return "Operator ID is required";
    }
    if (id.length < 3) {
      return "Operator ID must be at least 3 characters";
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
      return "Operator ID can only contain letters, numbers, hyphens, and underscores";
    }
    return null;
  };

  const validatePassword = (pwd: string): string | null => {
    if (!pwd) {
      return "Password is required";
    }
    if (pwd.length < 8) {
      return "Password must be at least 8 characters";
    }
    return null;
  };

  const checkPasswordStrength = (pwd: string) => {
    setPasswordStrength({
      hasMinLength: pwd.length >= 8,
      hasUpperCase: /[A-Z]/.test(pwd),
      hasLowerCase: /[a-z]/.test(pwd),
      hasNumber: /[0-9]/.test(pwd),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(pwd),
    });
  };

  const handleOperatorIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setOperatorId(value);

    if (touched.operatorId) {
      const error = validateOperatorId(value);
      if (error) {
        setErrors((prev) => [...prev.filter((e) => e.field !== "operatorId"), { field: "operatorId", message: error }]);
      } else {
        setErrors((prev) => prev.filter((e) => e.field !== "operatorId"));
      }
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
    checkPasswordStrength(value);

    if (touched.password) {
      const error = validatePassword(value);
      if (error) {
        setErrors((prev) => [...prev.filter((e) => e.field !== "password"), { field: "password", message: error }]);
      } else {
        setErrors((prev) => prev.filter((e) => e.field !== "password"));
      }
    }
  };

  const handleBlur = (field: "operatorId" | "password") => {
    setTouched((prev) => ({ ...prev, [field]: true }));

    if (field === "operatorId") {
      const error = validateOperatorId(operatorId);
      if (error) {
        setErrors((prev) => [...prev.filter((e) => e.field !== "operatorId"), { field: "operatorId", message: error }]);
      }
    } else {
      const error = validatePassword(password);
      if (error) {
        setErrors((prev) => [...prev.filter((e) => e.field !== "password"), { field: "password", message: error }]);
      }
    }
  };

  const startLockout = () => {
    setIsLockedOut(true);
    let timeRemaining = LOCKOUT_TIME / 1000;
    setLockoutTimer(timeRemaining);

    const interval = setInterval(() => {
      timeRemaining -= 1;
      setLockoutTimer(timeRemaining);

      if (timeRemaining <= 0) {
        clearInterval(interval);
        setIsLockedOut(false);
        setLoginAttempts(0);
        setErrors([]);
      }
    }, 1000);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLockedOut) {
      return;
    }

    // Mark all fields as touched
    setTouched({ operatorId: true, password: true });

    // Validate all fields
    const validationErrors: ValidationError[] = [];

    const operatorIdError = validateOperatorId(operatorId);
    if (operatorIdError) {
      validationErrors.push({ field: "operatorId", message: operatorIdError });
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      validationErrors.push({ field: "password", message: passwordError });
    }

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      audioSystem.playWarning();
      return;
    }

    setIsLoading(true);
    setErrors([]);
    setIsLoading(true);

    // Validate inputs
    const idError = validateOperatorId(operatorId);
    if (idError) {
      setErrors([{ field: 'operatorId', message: idError }]);
      setIsLoading(false);
      return;
    }

    const pwdError = validatePassword(password);
    if (pwdError) {
      setErrors([{ field: 'password', message: pwdError }]);
      setIsLoading(false);
      return;
    }

    try {
      // Call backend authentication API
      const apiBaseUrl = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://127.0.0.1:8001'
        : 'https://predictive-maintenance-api.onrender.com';

      const response = await fetch(`${apiBaseUrl}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          operator_id: operatorId,
          password: password
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Store session token and expiry
        const sessionToken = data.data.session_token;
        const sessionExpiry = data.data.session_expiry;
        const authenticatedUser = {
          operatorId: data.data.operator_id,
          role: data.data.role,
          loginTime: data.data.login_time
        };

        // Store session token in localStorage for persistent sessions
        localStorage.setItem("sessionToken", sessionToken);
        localStorage.setItem("sessionExpiry", sessionExpiry);

        // Remember Me functionality
        if (rememberMe) {
          localStorage.setItem("rememberedUser", JSON.stringify({
            operatorId: operatorId,
            lastLogin: new Date().toISOString(),
          }));
        } else {
          localStorage.removeItem("rememberedUser");
        }

        // Success - credentials meet all security requirements
        audioSystem.playSystemEvent();
        setIsLoading(false);

        // Store user info in sessionStorage
        sessionStorage.setItem("currentUser", JSON.stringify(authenticatedUser));
        navigate("/boot");
      } else {
        // Handle authentication errors
        setIsLoading(false);
        setErrors([{ field: 'general', message: data.message }]);

        // Handle lockout for too many attempts
        setLoginAttempts(prev => prev + 1);
        if (data.message?.includes('Invalid') && loginAttempts >= MAX_LOGIN_ATTEMPTS - 1) {
          setIsLockedOut(true);
          setLockoutTimer(LOCKOUT_TIME);
        }
      }

    } catch (err: any) {
      console.error("Login error:", err);
      setIsLoading(false);
      setErrors([{ field: 'general', message: err?.message ? `Login failed: ${err.message}` : "Login failed. Please try again." }]);
    }
  };

  const handleInputFocus = () => {
    if (!isLockedOut) {
      audioSystem.playHolographicInteraction();
    }
  };

  const getFieldError = (field: string) => {
    return errors.find((e) => e.field === field)?.message;
  };

  const getGeneralError = () => {
    return errors.find((e) => e.field === "general")?.message;
  };

  const hasFieldError = (field: string) => {
    return errors.some((e) => e.field === field);
  };

  const isFormValid = () => {
    return (
      operatorId.trim() &&
      password &&
      !hasFieldError("operatorId") &&
      !hasFieldError("password")
    );
  };

  const getPasswordStrengthScore = () => {
    const { hasMinLength, hasUpperCase, hasLowerCase, hasNumber, hasSpecialChar } = passwordStrength;
    let score = 0;
    if (hasMinLength) score++;
    if (hasUpperCase) score++;
    if (hasLowerCase) score++;
    if (hasNumber) score++;
    if (hasSpecialChar) score++;
    return score;
  };

  const getPasswordStrengthColor = () => {
    const score = getPasswordStrengthScore();
    if (score <= 2) return "red";
    if (score <= 3) return "orange";
    if (score <= 4) return "yellow";
    return "green";
  };

  const getPasswordStrengthLabel = () => {
    const score = getPasswordStrengthScore();
    if (score <= 2) return "Weak";
    if (score <= 3) return "Fair";
    if (score <= 4) return "Good";
    return "Strong";
  };

  // Format last login time
  const getLastLoginText = () => {
    if (!savedCredentials?.lastLogin) return "Never";
    const lastLogin = new Date(savedCredentials.lastLogin);
    const now = new Date();
    const diffMs = now.getTime() - lastLogin.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    return "Just now";
  };

  // Show loading while checking for existing session
  if (!autoLoginChecked) {
    return (
      <div className="relative size-full flex items-center justify-center overflow-hidden">
        <CinematicBackground />
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="relative z-10 text-center"
        >
          <motion.div
            className="w-16 h-16 mx-auto mb-4 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
          <p className="text-cyan-400 text-sm">Checking session...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="relative size-full flex items-center justify-center overflow-hidden">
      <CinematicBackground />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 w-full max-w-md mx-4"
      >
        {/* Main login card with glassmorphism */}
        <div className="relative backdrop-blur-xl bg-white/5 border border-cyan-500/30 rounded-2xl p-8 shadow-2xl">
          {/* Glowing border effect */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20 -z-10 blur-xl" />

          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 mb-4 border border-cyan-500/30"
              animate={{
                boxShadow: [
                  "0 0 20px rgba(6, 182, 212, 0.3)",
                  "0 0 40px rgba(6, 182, 212, 0.5)",
                  "0 0 20px rgba(6, 182, 212, 0.3)",
                ],
              }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Shield className="w-10 h-10 text-cyan-400" />
            </motion.div>
            <h1 className="text-3xl font-bold text-white mb-2">AI-POWERED</h1>
            <p className="text-cyan-400 text-sm tracking-wider">
              PREDICTIVE MAINTENANCE SYSTEM
            </p>
            <p className="text-gray-400 text-xs mt-1">
              Secure Industrial Intelligence System
            </p>
          </div>

          {/* System status indicators */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="backdrop-blur-sm bg-white/5 border border-cyan-500/20 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-green-400" />
                <span className="text-xs text-gray-400">System Status</span>
              </div>
              <p className="text-sm text-green-400 font-medium">Operational</p>
            </div>
            <div className="backdrop-blur-sm bg-white/5 border border-purple-500/20 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-gray-400">AI Core</span>
              </div>
              <p className="text-sm text-purple-400 font-medium">Active</p>
            </div>
          </div>

          {/* General Error Message */}
          <AnimatePresence>
            {getGeneralError() && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30"
              >
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-400">{getGeneralError()}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Lockout Message */}
          {isLockedOut && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mb-4 p-4 rounded-lg bg-red-500/20 border-2 border-red-500/50"
            >
              <div className="flex items-center gap-3">
                <motion.div
                  animate={{ rotate: [0, 5, -5, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                >
                  <Lock className="w-6 h-6 text-red-400" />
                </motion.div>
                <div>
                  <p className="text-sm font-bold text-red-400">Account Locked</p>
                  <p className="text-xs text-red-300">
                    Please wait {lockoutTimer} seconds before trying again
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Login form */}
          <form onSubmit={handleLogin} className="space-y-4">
            {/* Operator ID Field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Operator ID <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={operatorId}
                  onChange={handleOperatorIdChange}
                  onFocus={handleInputFocus}
                  onBlur={() => handleBlur("operatorId")}
                  disabled={isLockedOut || isLoading}
                  className={`w-full px-4 py-3 pr-10 bg-white/5 border rounded-lg text-white placeholder-gray-500 focus:outline-none transition-all ${hasFieldError("operatorId")
                      ? "border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                      : touched.operatorId && operatorId && !hasFieldError("operatorId")
                        ? "border-green-500/50 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                        : "border-cyan-500/30 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                    } ${isLockedOut || isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                  placeholder="Enter operator ID"
                  autoComplete="username"
                />
                {touched.operatorId && operatorId && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    {hasFieldError("operatorId") ? (
                      <XCircle className="w-5 h-5 text-red-400" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-green-400" />
                    )}
                  </div>
                )}
              </div>
              <AnimatePresence>
                {getFieldError("operatorId") && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="text-xs text-red-400 mt-1 flex items-center gap-1"
                  >
                    <AlertCircle className="w-3 h-3" />
                    {getFieldError("operatorId")}
                  </motion.p>
                )}
              </AnimatePresence>
              {!hasFieldError("operatorId") && (
                <p className="text-xs text-gray-500 mt-1">
                  3+ characters, alphanumeric and hyphens only
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">
                Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={handlePasswordChange}
                  onFocus={handleInputFocus}
                  onBlur={() => handleBlur("password")}
                  disabled={isLockedOut || isLoading}
                  className={`w-full px-4 py-3 pr-10 bg-white/5 border rounded-lg text-white placeholder-gray-500 focus:outline-none transition-all ${hasFieldError("password")
                      ? "border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500"
                      : touched.password && password && !hasFieldError("password")
                        ? "border-green-500/50 focus:border-green-500 focus:ring-1 focus:ring-green-500"
                        : "border-cyan-500/30 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
                    } ${isLockedOut || isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                  placeholder="Enter password"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLockedOut || isLoading}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-cyan-400 transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
              <AnimatePresence>
                {getFieldError("password") && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="text-xs text-red-400 mt-1 flex items-center gap-1"
                  >
                    <AlertCircle className="w-3 h-3" />
                    {getFieldError("password")}
                  </motion.p>
                )}
              </AnimatePresence>

              {/* Password Strength Indicator */}
              {password && !hasFieldError("password") && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mt-2"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400">Password Strength:</span>
                    <span
                      className={`text-xs font-medium ${getPasswordStrengthColor() === "green"
                          ? "text-green-400"
                          : getPasswordStrengthColor() === "yellow"
                            ? "text-yellow-400"
                            : getPasswordStrengthColor() === "orange"
                              ? "text-orange-400"
                              : "text-red-400"
                        }`}
                    >
                      {getPasswordStrengthLabel()}
                    </span>
                  </div>
                  <div className="flex gap-1 mb-2">
                    {[1, 2, 3, 4, 5].map((index) => (
                      <div
                        key={index}
                        className={`h-1 flex-1 rounded-full transition-all ${index <= getPasswordStrengthScore()
                            ? getPasswordStrengthColor() === "green"
                              ? "bg-green-500"
                              : getPasswordStrengthColor() === "yellow"
                                ? "bg-yellow-500"
                                : getPasswordStrengthColor() === "orange"
                                  ? "bg-orange-500"
                                  : "bg-red-500"
                            : "bg-gray-700"
                          }`}
                      />
                    ))}
                  </div>
                  <div className="space-y-1">
                    {[
                      { label: "At least 8 characters", met: passwordStrength.hasMinLength },
                      { label: "Uppercase letter", met: passwordStrength.hasUpperCase },
                      { label: "Lowercase letter", met: passwordStrength.hasLowerCase },
                      { label: "Number", met: passwordStrength.hasNumber },
                      { label: "Special character", met: passwordStrength.hasSpecialChar },
                    ].map((req, index) => (
                      <div key={index} className="flex items-center gap-2">
                        {req.met ? (
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                        ) : (
                          <XCircle className="w-3 h-3 text-gray-600" />
                        )}
                        <span
                          className={`text-xs ${req.met ? "text-green-400" : "text-gray-500"
                            }`}
                        >
                          {req.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Remember Me & Quick Actions */}
            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  disabled={isLockedOut || isLoading}
                  className="w-4 h-4 rounded border-cyan-500/30 bg-white/5 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0 cursor-pointer"
                />
                <span className="text-sm text-gray-400 group-hover:text-cyan-400 transition-colors">
                  Remember me
                </span>
              </label>
              <button
                type="button"
                className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                Forgot password?
              </button>
            </div>

            <motion.button
              type="submit"
              disabled={isLockedOut || isLoading || !isFormValid()}
              whileHover={!isLockedOut && !isLoading && isFormValid() ? { scale: 1.02 } : {}}
              whileTap={!isLockedOut && !isLoading && isFormValid() ? { scale: 0.98 } : {}}
              className={`w-full py-3 rounded-lg font-medium shadow-lg transition-all flex items-center justify-center gap-2 ${isLockedOut || isLoading || !isFormValid()
                  ? "bg-gray-500/20 text-gray-500 cursor-not-allowed"
                  : "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-cyan-500/30 hover:shadow-cyan-500/50"
                }`}
            >
              {isLoading ? (
                <>
                  <motion.div
                    className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                  Authenticating...
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  Authenticate
                </>
              )}
            </motion.button>
          </form>

          {/* Footer info */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>Last login: {getLastLoginText()}</span>
              <span className="text-cyan-400">🔒 Session encrypted</span>
            </div>
            {savedCredentials && (
              <div className="mt-2 text-xs text-green-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Welcome back, {savedCredentials.operatorId}!</span>
              </div>
            )}
          </div>


          {/* Security notice */}
          <motion.div
            className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
            animate={{
              borderColor: [
                "rgba(239, 68, 68, 0.3)",
                "rgba(239, 68, 68, 0.5)",
                "rgba(239, 68, 68, 0.3)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <p className="text-xs text-red-400 text-center">
              ⚠ AUTHORIZED ACCESS ONLY
            </p>
            <p className="text-xs text-red-300 text-center mt-1">
              {loginAttempts > 0 && `Failed attempts: ${loginAttempts}/${MAX_LOGIN_ATTEMPTS}`}
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
