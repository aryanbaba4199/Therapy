import React, { useState } from "react";
import {
  Alert,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Step,
  StepLabel,
  Stepper,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import {
  FiArrowLeft,
  FiArrowRight,
  FiCheck,
  FiCopy,
  FiPlus,
  FiTrash2,
  FiUserCheck,
} from "react-icons/fi";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useOnboardTherapistMutation } from "../api/operations_api";
import type {
  OnboardTherapistAvailabilityRequest,
  OnboardTherapistRequest,
  OnboardTherapistResponse,
} from "../types/operations_types";

interface IntervalInput {
  start_time: string;
  end_time: string;
  session_modes: string[];
}

export const TherapistOnboardingPage: React.FC = () => {
  const { t } = useTranslation(["operations", "therapist", "common"]);
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);

  // Step 1: Account
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [useCustomPassword, setUseCustomPassword] = useState(false);
  const [temporaryPassword, setTemporaryPassword] = useState("");

  // Step 2: Profile
  const [displayName, setDisplayName] = useState("");
  const [designation, setDesignation] = useState(
    "Consultant Clinical Psychologist"
  );
  const [specialization, setSpecialization] = useState("clinical_psychologist");
  const [bio, setBio] = useState("");
  const [qualificationsStr, setQualificationsStr] = useState(
    "M.Phil Clinical Psychology"
  );
  const [experienceYears, setExperienceYears] = useState(5);
  const [therapyHours, setTherapyHours] = useState(500);
  const [languagesStr, setLanguagesStr] = useState("English, Malayalam");
  const [expertisesStr, setExpertisesStr] = useState("CBT, Anxiety, Trauma");
  const [sessionModes, setSessionModes] = useState<string[]>(["online"]);
  const [profileImageUrl, setProfileImageUrl] = useState("");

  // Step 3: Pricing
  const [amount, setAmount] = useState(1500);
  const [currency] = useState("INR");
  const [durationMinutes, setDurationMinutes] = useState(50);

  // Step 4: Verification
  const [verificationStatus, setVerificationStatus] = useState<
    "pending" | "verified"
  >("pending");
  const [regNumber, setRegNumber] = useState("");
  const [regAuthority, setRegAuthority] = useState(
    "Rehabilitation Council of India"
  );

  // Step 5: Availability
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [scheduleDays, setScheduleDays] = useState<
    Record<number, IntervalInput[]>
  >({
    1: [{ start_time: "10:00", end_time: "13:00", session_modes: ["online"] }],
    2: [{ start_time: "10:00", end_time: "13:00", session_modes: ["online"] }],
    3: [{ start_time: "10:00", end_time: "13:00", session_modes: ["online"] }],
    4: [{ start_time: "10:00", end_time: "13:00", session_modes: ["online"] }],
    5: [{ start_time: "10:00", end_time: "13:00", session_modes: ["online"] }],
  });

  // Step 6: Review & Final
  const [activationMode, setActivationMode] = useState<"draft" | "active">(
    "draft"
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Success Modal
  const [onboardResponse, setOnboardResponse] =
    useState<OnboardTherapistResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const [onboardTherapist, { isLoading: isSubmitting }] =
    useOnboardTherapistMutation();

  const steps = [
    t("operations:onboarding.steps.account", "Account"),
    t("operations:onboarding.steps.profile", "Profile"),
    t("operations:onboarding.steps.pricing", "Consultation"),
    t("operations:onboarding.steps.verification", "Credentials"),
    t("operations:onboarding.steps.availability", "Availability"),
    t("operations:onboarding.steps.review", "Review"),
  ];

  const handleNext = () => {
    setErrorMsg(null);
    if (activeStep === 0) {
      if (
        !firstName.trim() ||
        !lastName.trim() ||
        !email.trim() ||
        !phone.trim()
      ) {
        setErrorMsg("Please fill out all required account fields.");
        return;
      }
    } else if (activeStep === 1) {
      if (!bio.trim() || bio.trim().length < 10) {
        setErrorMsg("Bio must be at least 10 characters long.");
        return;
      }
      if (sessionModes.length === 0) {
        setErrorMsg("Please select at least one session delivery mode.");
        return;
      }
    } else if (activeStep === 2) {
      if (amount < 0 || durationMinutes < 15) {
        setErrorMsg("Please specify valid consultation amount and duration.");
        return;
      }
    }
    setActiveStep((prev) => Math.min(prev + 1, steps.length - 1));
  };

  const handleBack = () => {
    setErrorMsg(null);
    setActiveStep((prev) => Math.max(prev - 1, 0));
  };

  const addIntervalToDay = (day: number) => {
    setScheduleDays((prev) => ({
      ...prev,
      [day]: [
        ...(prev[day] || []),
        { start_time: "14:00", end_time: "17:00", session_modes: ["online"] },
      ],
    }));
  };

  const removeIntervalFromDay = (day: number, index: number) => {
    setScheduleDays((prev) => ({
      ...prev,
      [day]: (prev[day] || []).filter((_, i) => i !== index),
    }));
  };

  const updateInterval = (
    day: number,
    index: number,
    field: "start_time" | "end_time",
    val: string
  ) => {
    setScheduleDays((prev) => {
      const currentList = prev[day] || [];
      const current = currentList[index];
      if (!current) return prev;
      const updatedItem: IntervalInput = {
        start_time: field === "start_time" ? val : current.start_time,
        end_time: field === "end_time" ? val : current.end_time,
        session_modes: current.session_modes,
      };
      const updatedList = [...currentList];
      updatedList[index] = updatedItem;
      return { ...prev, [day]: updatedList };
    });
  };

  const handleSubmit = async () => {
    setErrorMsg(null);

    if (activationMode === "active" && verificationStatus !== "verified") {
      setErrorMsg(
        t(
          "operations:onboarding.review.activationWarning",
          "Activation requires credentials status to be 'Verified & Approved'."
        )
      );
      return;
    }

    const quals = qualificationsStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const langs = languagesStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const exps = expertisesStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const formattedDays = Object.entries(scheduleDays)
      .filter(([_, intervals]) => intervals && intervals.length > 0)
      .map(([dayStr, intervals]) => ({
        day_of_week: Number(dayStr),
        intervals: intervals.map((i) => ({
          start_time: i.start_time,
          end_time: i.end_time,
          session_modes: i.session_modes,
        })),
      }));

    const availabilityPayload: OnboardTherapistAvailabilityRequest = {
      timezone,
      days: formattedDays,
    };

    const payload: OnboardTherapistRequest = {
      account: {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        temporary_password: useCustomPassword
          ? temporaryPassword.trim() || undefined
          : undefined,
      },
      profile: {
        display_name: displayName.trim() || undefined,
        bio: bio.trim(),
        designation: designation.trim(),
        specialization,
        qualifications: quals.length > 0 ? quals : ["Consultant"],
        experience_years: experienceYears,
        therapy_hours: therapyHours,
        languages: langs.length > 0 ? langs : ["en"],
        expertises: exps.length > 0 ? exps : ["General Counseling"],
        session_modes: sessionModes,
        profile_image_url: profileImageUrl.trim() || undefined,
      },
      pricing: {
        amount,
        currency,
        duration_minutes: durationMinutes,
      },
      verification: {
        status: verificationStatus,
        registration_number: regNumber.trim() || undefined,
        registration_authority: regAuthority.trim() || undefined,
      },
      availability: formattedDays.length > 0 ? availabilityPayload : undefined,
      status: activationMode,
    };

    try {
      const res = await onboardTherapist(payload).unwrap();
      if (res.data) {
        setOnboardResponse(res.data);
      }
    } catch (err: unknown) {
      const apiErr = err as { data?: { error?: { message?: string } } };
      setErrorMsg(
        apiErr?.data?.error?.message ||
          "Failed to onboard therapist. Please review inputs."
      );
    }
  };

  const copyCredentials = () => {
    if (!onboardResponse) return;
    const text = `Therapy Practitioner Account Credentials:\nEmail: ${onboardResponse.email}\nTemporary Password: ${onboardResponse.temporary_password}\nStatus: ${onboardResponse.status}`;
    void navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  return (
    <Container maxWidth="lg" className="py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Button
            variant="text"
            startIcon={<FiArrowLeft />}
            onClick={() => navigate("/operations/therapists")}
            className="mb-2 text-neutral-600 hover:text-neutral-900"
          >
            {t("operations:onboarding.backToList", "Back to Therapists")}
          </Button>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("operations:onboarding.title", "Therapist Onboarding Wizard")}
          </Typography>
          <Typography variant="body1" className="text-neutral-500 mt-1">
            {t(
              "operations:onboarding.subtitle",
              "Provision new clinical practitioners, configure credentials, initial fees, and availability schedules."
            )}
          </Typography>
        </div>
      </div>

      {/* Stepper Card */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-6">
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {errorMsg && (
        <Alert severity="error" className="rounded-xl">
          {errorMsg}
        </Alert>
      )}

      {/* Step Contents */}
      <Card className="rounded-2xl border border-neutral-200 shadow-xs">
        <CardContent className="p-6 sm:p-8 space-y-6">
          {/* STEP 0: Account */}
          {activeStep === 0 && (
            <div className="space-y-6">
              <Typography variant="h6" className="font-bold text-neutral-900">
                {t(
                  "operations:onboarding.account.title",
                  "Account & Authentication"
                )}
              </Typography>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  fullWidth
                  required
                  label={t(
                    "operations:onboarding.account.firstName",
                    "First Name"
                  )}
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
                <TextField
                  fullWidth
                  required
                  label={t(
                    "operations:onboarding.account.lastName",
                    "Last Name"
                  )}
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
                <TextField
                  fullWidth
                  required
                  type="email"
                  label={t(
                    "operations:onboarding.account.email",
                    "Email Address"
                  )}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <TextField
                  fullWidth
                  required
                  label={t(
                    "operations:onboarding.account.phone",
                    "Mobile Number"
                  )}
                  placeholder="+919876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>

              <Divider className="my-4" />

              <div className="space-y-3">
                <FormControlLabel
                  control={
                    <Switch
                      checked={useCustomPassword}
                      onChange={(e) => setUseCustomPassword(e.target.checked)}
                    />
                  }
                  label={t(
                    "operations:onboarding.account.customPassword",
                    "Set custom temporary password"
                  )}
                />
                {useCustomPassword && (
                  <TextField
                    fullWidth
                    label={t(
                      "operations:onboarding.account.tempPassword",
                      "Temporary Password"
                    )}
                    value={temporaryPassword}
                    onChange={(e) => setTemporaryPassword(e.target.value)}
                    helperText="If omitted or left empty, a secure password will be generated automatically."
                  />
                )}
              </div>
            </div>
          )}

          {/* STEP 1: Profile */}
          {activeStep === 1 && (
            <div className="space-y-6">
              <Typography variant="h6" className="font-bold text-neutral-900">
                {t(
                  "operations:onboarding.profile.title",
                  "Professional Profile"
                )}
              </Typography>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.profile.displayName",
                    "Display Name"
                  )}
                  placeholder="e.g. Dr. Ananya Menon"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
                <TextField
                  fullWidth
                  required
                  label={t(
                    "operations:onboarding.profile.designation",
                    "Designation"
                  )}
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                />
                <FormControl fullWidth>
                  <InputLabel id="spec-label">
                    {t(
                      "operations:onboarding.profile.specialization",
                      "Specialization"
                    )}
                  </InputLabel>
                  <Select
                    labelId="spec-label"
                    value={specialization}
                    label={t(
                      "operations:onboarding.profile.specialization",
                      "Specialization"
                    )}
                    onChange={(e) => setSpecialization(e.target.value)}
                  >
                    <MenuItem value="clinical_psychologist">
                      Clinical Psychologist
                    </MenuItem>
                    <MenuItem value="consultant_psychologist">
                      Consultant Psychologist
                    </MenuItem>
                    <MenuItem value="sexual_health_specialist">
                      Sexual Health Specialist
                    </MenuItem>
                    <MenuItem value="psychiatrist">Psychiatrist</MenuItem>
                  </Select>
                </FormControl>
                <div className="grid grid-cols-2 gap-2">
                  <TextField
                    fullWidth
                    type="number"
                    label={t(
                      "operations:onboarding.profile.experienceYears",
                      "Experience (Yrs)"
                    )}
                    value={experienceYears}
                    onChange={(e) => setExperienceYears(Number(e.target.value))}
                  />
                  <TextField
                    fullWidth
                    type="number"
                    label={t(
                      "operations:onboarding.profile.therapyHours",
                      "Therapy Hours"
                    )}
                    value={therapyHours}
                    onChange={(e) => setTherapyHours(Number(e.target.value))}
                  />
                </div>
                <div className="sm:col-span-2">
                  <TextField
                    fullWidth
                    required
                    multiline
                    rows={3}
                    label={t(
                      "operations:onboarding.profile.bio",
                      "Professional Bio"
                    )}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                  />
                </div>
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.profile.qualifications",
                    "Qualifications"
                  )}
                  value={qualificationsStr}
                  onChange={(e) => setQualificationsStr(e.target.value)}
                  helperText="Comma separated values"
                />
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.profile.languages",
                    "Languages Spoken"
                  )}
                  value={languagesStr}
                  onChange={(e) => setLanguagesStr(e.target.value)}
                  helperText="Comma separated values"
                />
                <div className="sm:col-span-2">
                  <TextField
                    fullWidth
                    label={t(
                      "operations:onboarding.profile.expertises",
                      "Areas of Expertise"
                    )}
                    value={expertisesStr}
                    onChange={(e) => setExpertisesStr(e.target.value)}
                    helperText="Comma separated values"
                  />
                </div>
                <FormControl fullWidth>
                  <InputLabel id="modes-label">
                    {t(
                      "operations:onboarding.profile.sessionModes",
                      "Session Delivery Modes"
                    )}
                  </InputLabel>
                  <Select
                    labelId="modes-label"
                    multiple
                    value={sessionModes}
                    label={t(
                      "operations:onboarding.profile.sessionModes",
                      "Session Delivery Modes"
                    )}
                    onChange={(e) => {
                      const val = e.target.value;
                      setSessionModes(
                        typeof val === "string" ? val.split(",") : val
                      );
                    }}
                  >
                    <MenuItem value="online">Online Video/Audio</MenuItem>
                    <MenuItem value="offline_bangalore">
                      In-Person (Bangalore)
                    </MenuItem>
                    <MenuItem value="offline_kozhikode">
                      In-Person (Kozhikode)
                    </MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.profile.profileImageUrl",
                    "Avatar URL"
                  )}
                  value={profileImageUrl}
                  onChange={(e) => setProfileImageUrl(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* STEP 2: Pricing */}
          {activeStep === 2 && (
            <div className="space-y-6">
              <Typography variant="h6" className="font-bold text-neutral-900">
                {t(
                  "operations:onboarding.pricing.title",
                  "Consultation Settings"
                )}
              </Typography>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <TextField
                  fullWidth
                  required
                  type="number"
                  label={t(
                    "operations:onboarding.pricing.amount",
                    "Session Fee (INR)"
                  )}
                  value={amount}
                  onChange={(e) => setAmount(Number(e.target.value))}
                />
                <TextField
                  fullWidth
                  label="Currency"
                  value={currency}
                  disabled
                />
                <TextField
                  fullWidth
                  required
                  type="number"
                  label={t(
                    "operations:onboarding.pricing.duration",
                    "Duration (Minutes)"
                  )}
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                />
              </div>
            </div>
          )}

          {/* STEP 3: Verification */}
          {activeStep === 3 && (
            <div className="space-y-6">
              <Typography variant="h6" className="font-bold text-neutral-900">
                {t(
                  "operations:onboarding.verification.title",
                  "Credentials & License Verification"
                )}
              </Typography>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.verification.regNumber",
                    "Registration Number"
                  )}
                  placeholder="e.g. RCI-CR-2024-XXXX"
                  value={regNumber}
                  onChange={(e) => setRegNumber(e.target.value)}
                />
                <TextField
                  fullWidth
                  label={t(
                    "operations:onboarding.verification.regAuthority",
                    "Authority / Council"
                  )}
                  value={regAuthority}
                  onChange={(e) => setRegAuthority(e.target.value)}
                />
                <div className="sm:col-span-2">
                  <FormControl fullWidth>
                    <InputLabel id="verify-status-label">
                      {t(
                        "operations:onboarding.verification.status",
                        "Verification Status"
                      )}
                    </InputLabel>
                    <Select
                      labelId="verify-status-label"
                      value={verificationStatus}
                      label={t(
                        "operations:onboarding.verification.status",
                        "Verification Status"
                      )}
                      onChange={(e) =>
                        setVerificationStatus(
                          e.target.value as "pending" | "verified"
                        )
                      }
                    >
                      <MenuItem value="pending">
                        {t(
                          "operations:onboarding.verification.statusPending",
                          "Pending Verification"
                        )}
                      </MenuItem>
                      <MenuItem value="verified">
                        {t(
                          "operations:onboarding.verification.statusVerified",
                          "Verified & Approved"
                        )}
                      </MenuItem>
                    </Select>
                    <FormHelperText>
                      Setting status to Verified & Approved allows practitioner
                      profile to be directly activated.
                    </FormHelperText>
                  </FormControl>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Availability */}
          {activeStep === 4 && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <Typography variant="h6" className="font-bold text-neutral-900">
                  {t(
                    "operations:onboarding.availability.title",
                    "Initial Availability Schedule"
                  )}
                </Typography>
                <TextField
                  size="small"
                  label={t(
                    "operations:onboarding.availability.timezone",
                    "Timezone"
                  )}
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                />
              </div>

              <div className="space-y-4">
                {[1, 2, 3, 4, 5, 6, 0].map((dayNum) => {
                  const intervals = scheduleDays[dayNum] || [];
                  const dayName = t(
                    `operations:onboarding.availability.days.${dayNum}`,
                    `Day ${dayNum}`
                  );
                  return (
                    <div
                      key={dayNum}
                      className="p-4 border border-neutral-200 rounded-xl space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <Typography
                          variant="subtitle1"
                          className="font-bold text-neutral-800"
                        >
                          {dayName}
                        </Typography>
                        <Button
                          size="small"
                          startIcon={<FiPlus />}
                          onClick={() => addIntervalToDay(dayNum)}
                        >
                          {t(
                            "operations:onboarding.availability.addInterval",
                            "Add Slot"
                          )}
                        </Button>
                      </div>

                      {intervals.length === 0 ? (
                        <Typography
                          variant="body2"
                          className="text-neutral-400 italic"
                        >
                          {t(
                            "operations:onboarding.availability.noSlots",
                            "No slots scheduled"
                          )}
                        </Typography>
                      ) : (
                        <div className="space-y-2">
                          {intervals.map((intv, idx) => (
                            <div key={idx} className="flex items-center gap-3">
                              <TextField
                                size="small"
                                type="time"
                                label="Start"
                                slotProps={{ inputLabel: { shrink: true } }}
                                value={intv.start_time}
                                onChange={(e) =>
                                  updateInterval(
                                    dayNum,
                                    idx,
                                    "start_time",
                                    e.target.value
                                  )
                                }
                              />
                              <TextField
                                size="small"
                                type="time"
                                label="End"
                                slotProps={{ inputLabel: { shrink: true } }}
                                value={intv.end_time}
                                onChange={(e) =>
                                  updateInterval(
                                    dayNum,
                                    idx,
                                    "end_time",
                                    e.target.value
                                  )
                                }
                              />
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() =>
                                  removeIntervalFromDay(dayNum, idx)
                                }
                              >
                                <FiTrash2 />
                              </IconButton>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 5: Review & Submit */}
          {activeStep === 5 && (
            <div className="space-y-6">
              <Typography variant="h6" className="font-bold text-neutral-900">
                {t(
                  "operations:onboarding.review.title",
                  "Review & Complete Onboarding"
                )}
              </Typography>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-neutral-50 p-4 rounded-xl border border-neutral-200 text-sm">
                <div>
                  <span className="font-semibold text-neutral-600">
                    Practitioner:
                  </span>{" "}
                  {displayName || `${firstName} ${lastName}`}
                </div>
                <div>
                  <span className="font-semibold text-neutral-600">Email:</span>{" "}
                  {email}
                </div>
                <div>
                  <span className="font-semibold text-neutral-600">Phone:</span>{" "}
                  {phone}
                </div>
                <div>
                  <span className="font-semibold text-neutral-600">
                    Specialization:
                  </span>{" "}
                  {specialization}
                </div>
                <div>
                  <span className="font-semibold text-neutral-600">Fee:</span> ₹
                  {amount} / {durationMinutes} min
                </div>
                <div>
                  <span className="font-semibold text-neutral-600">
                    Verification:
                  </span>{" "}
                  <span
                    className={
                      verificationStatus === "verified"
                        ? "text-emerald-600 font-bold"
                        : "text-amber-600 font-bold"
                    }
                  >
                    {verificationStatus === "verified" ? "Verified" : "Pending"}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <Typography
                  variant="subtitle1"
                  className="font-bold text-neutral-800"
                >
                  Initial Publication Status:
                </Typography>
                <RadioGroup
                  row
                  value={activationMode}
                  onChange={(e) =>
                    setActivationMode(e.target.value as "draft" | "active")
                  }
                >
                  <FormControlLabel
                    value="draft"
                    control={<Radio />}
                    label={t(
                      "operations:onboarding.review.draftMode",
                      "Save as Draft"
                    )}
                  />
                  <FormControlLabel
                    value="active"
                    control={<Radio />}
                    label={t(
                      "operations:onboarding.review.activateMode",
                      "Create & Activate Immediately"
                    )}
                  />
                </RadioGroup>
                {activationMode === "active" &&
                  verificationStatus !== "verified" && (
                    <Alert severity="warning" className="rounded-xl">
                      {t(
                        "operations:onboarding.review.activationWarning",
                        "Activation requires credentials status to be 'Verified & Approved'."
                      )}
                    </Alert>
                  )}
              </div>
            </div>
          )}

          {/* Navigation Actions */}
          <div className="flex items-center justify-between pt-6 border-t border-neutral-200">
            <Button
              variant="outlined"
              disabled={activeStep === 0 || isSubmitting}
              onClick={handleBack}
              startIcon={<FiArrowLeft />}
            >
              Back
            </Button>

            {activeStep < steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<FiArrowRight />}
              >
                Next
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                disabled={isSubmitting}
                onClick={handleSubmit}
                startIcon={
                  isSubmitting ? (
                    <CircularProgress size={16} />
                  ) : (
                    <FiUserCheck />
                  )
                }
              >
                {isSubmitting
                  ? t(
                      "operations:onboarding.review.submitting",
                      "Provisioning..."
                    )
                  : t(
                      "operations:onboarding.review.submit",
                      "Complete Onboarding"
                    )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Success Modal */}
      <Dialog open={Boolean(onboardResponse)} maxWidth="sm" fullWidth>
        <DialogTitle className="font-bold flex items-center gap-2 text-emerald-600">
          <FiCheck className="text-xl" />
          {t(
            "operations:onboarding.success.title",
            "Therapist Successfully Onboarded!"
          )}
        </DialogTitle>
        <DialogContent className="space-y-4 pt-2">
          <Typography variant="body2" className="text-neutral-600">
            {t(
              "operations:onboarding.success.credentialsNote",
              "Please share these initial credentials securely with the therapist."
            )}
          </Typography>

          <div className="bg-neutral-100 p-4 rounded-xl space-y-2 font-mono text-sm border border-neutral-200">
            <div>
              <span className="text-neutral-500">Email:</span>{" "}
              <span className="font-bold text-neutral-800">
                {onboardResponse?.email}
              </span>
            </div>
            <div>
              <span className="text-neutral-500">Temporary Password:</span>{" "}
              <span className="font-bold text-indigo-700">
                {onboardResponse?.temporary_password}
              </span>
            </div>
            <div>
              <span className="text-neutral-500">Status:</span>{" "}
              <span className="font-bold text-neutral-800">
                {onboardResponse?.status}
              </span>
            </div>
          </div>
        </DialogContent>
        <DialogActions className="p-4 gap-2 flex-wrap">
          <Button
            variant="outlined"
            startIcon={copied ? <FiCheck /> : <FiCopy />}
            onClick={copyCredentials}
          >
            {copied ? "Copied!" : "Copy Credentials"}
          </Button>
          <Button
            variant="outlined"
            color="primary"
            onClick={() => navigate("/therapists")}
          >
            View Directory
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate("/operations/therapists")}
          >
            {t("operations:onboarding.success.done", "Manage Therapists")}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};
