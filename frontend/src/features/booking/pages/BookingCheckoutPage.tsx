import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Divider,
  Radio,
  RadioGroup,
  FormControlLabel,
  TextField,
  Typography,
  Chip,
} from "@mui/material";
import {
  FiCheckCircle,
  FiShield,
  FiXCircle,
  FiTag,
  FiCreditCard,
} from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  useCancelReservationMutation,
  useGetReservationQuery,
} from "../api/booking_api";
import { ReservationTimer } from "../components/ReservationTimer";
import { useGetMeQuery } from "@/features/auth/api/auth_api";
import { useGetTherapistQuery } from "@/features/therapist/api/therapist_api";
import { useValidateOfferMutation } from "@/features/offer/api/offer_api";
import { useListMyUsablePackagesQuery } from "@/features/package/api/package_api";
import {
  useGetPaymentConfigQuery,
  useInitiatePaymentMutation,
  useVerifyPaymentMutation,
} from "@/features/payment/api/payment_api";
import type {
  RazorpayCheckoutOptions,
  RazorpayFailureResponse,
  RazorpaySuccessResponse,
} from "@/features/payment/types/razorpay";

export const BookingCheckoutPage: React.FC = () => {
  const { t } = useTranslation(["booking", "payment", "offer"]);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const reservationId = searchParams.get("reservationId") || "";

  const [notes, setNotes] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Commerce states
  const [couponInput, setCouponInput] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState<string | null>(null);
  const [discountMinor, setDiscountMinor] = useState(0);
  const [selectedPackageId, setSelectedPackageId] = useState<string | null>(
    null
  );
  const [paymentMethod, setPaymentMethod] = useState<
    "upi" | "card" | "netbanking" | "package_redemption"
  >("upi");

  const {
    data: resData,
    isLoading: isResLoading,
    error: resError,
  } = useGetReservationQuery(reservationId, {
    skip: !reservationId,
    pollingInterval: 15000,
  });

  const reservation = resData?.data;

  const { data: therapistData } = useGetTherapistQuery(
    reservation?.therapist_id || "",
    {
      skip: !reservation?.therapist_id,
    }
  );
  const therapist = therapistData?.data;
  const basePriceMinor = therapist
    ? Math.round(therapist.pricing.amount * 100)
    : 0;

  // Available packages for current user
  const { data: usablePackagesData } = useListMyUsablePackagesQuery();
  const usablePackages = usablePackagesData?.data || [];

  const { data: paymentConfigData } = useGetPaymentConfigQuery();
  const { data: meData } = useGetMeQuery();
  const currentUser = meData?.data;

  const [validateOffer, { isLoading: isValidatingOffer }] =
    useValidateOfferMutation();
  const [initiatePayment, { isLoading: isInitiatingPayment }] =
    useInitiatePaymentMutation();
  const [verifyPayment, { isLoading: isVerifyingPayment }] =
    useVerifyPaymentMutation();
  const [cancelReservation, { isLoading: isCancelling }] =
    useCancelReservationMutation();

  const isProcessing = isInitiatingPayment || isVerifyingPayment;

  // Recalculate payable amount
  const payableMinor = selectedPackageId
    ? 0
    : Math.max(0, basePriceMinor - discountMinor);

  useEffect(() => {
    if (selectedPackageId) {
      setPaymentMethod("package_redemption");
    } else if (paymentMethod === "package_redemption") {
      setPaymentMethod("upi");
    }
  }, [selectedPackageId, paymentMethod]);

  const handleApplyCoupon = async () => {
    if (!couponInput.trim()) return;
    try {
      setErrorMessage(null);
      const res = await validateOffer({
        code: couponInput.trim().toUpperCase(),
        base_amount_minor: basePriceMinor,
      }).unwrap();
      if (res.data && res.data.offer_applied) {
        setAppliedCoupon(res.data.offer_applied.code);
        setDiscountMinor(res.data.discount_amount_minor);
      }
    } catch (err: unknown) {
      const errorObj = err as { data?: { message?: string } };
      setErrorMessage(errorObj.data?.message || "Invalid coupon code");
    }
  };

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null);
    setDiscountMinor(0);
    setCouponInput("");
  };

  const handleSelectPackage = (pkgId: string) => {
    if (selectedPackageId === pkgId) {
      setSelectedPackageId(null);
    } else {
      setSelectedPackageId(pkgId);
      setAppliedCoupon(null);
      setDiscountMinor(0);
      setCouponInput("");
    }
  };

  const handlePaymentSubmit = async () => {
    if (!reservation) return;
    try {
      setErrorMessage(null);

      // 1. Initiate payment intent
      const initRes = await initiatePayment({
        target_type: "booking",
        target_id: reservation.id,
        payment_method: paymentMethod,
        offer_code: appliedCoupon || undefined,
        user_package_id: selectedPackageId || undefined,
        idempotency_key: `booking-pay-${reservation.id}`,
      }).unwrap();

      const payment = initRes.data;
      if (!payment) {
        throw new Error("Failed to initiate payment");
      }

      // If package redemption, it's paid immediately with 0 minor amount!
      if (payment.status === "paid") {
        const confirmedBookingId = payment.booking_id || reservation.id;
        navigate(`/bookings/confirmation?bookingId=${confirmedBookingId}`);
        return;
      }

      // 2. Determine payment provider: Razorpay or Mock
      const config = paymentConfigData?.data;
      const isRazorpay =
        payment.provider === "razorpay" ||
        config?.payment_provider === "razorpay";

      if (isRazorpay && window.Razorpay) {
        // Open Razorpay Standard Checkout
        const keyId = config?.razorpay_key_id || "";
        const options: RazorpayCheckoutOptions = {
          key: keyId,
          amount: payment.amount_minor,
          currency: payment.currency || "INR",
          name: "Manaswell",
          description: `Therapy Consultation with ${therapist?.display_name || "Therapist"}`,
          order_id: payment.provider_order_id,
          prefill: {
            name:
              `${currentUser?.first_name || ""} ${currentUser?.last_name || ""}`.trim() ||
              undefined,
            email: currentUser?.email || undefined,
            contact: currentUser?.phone || undefined,
          },
          theme: {
            color: "#0d9488", // teal-600
          },
          modal: {
            ondismiss: () => {
              setErrorMessage(
                t("payment:paymentCancelled") || "Payment cancelled by user"
              );
            },
          },
          handler: async (response: RazorpaySuccessResponse) => {
            try {
              const verifyRes = await verifyPayment({
                paymentId: payment.id,
                body: {
                  provider_order_id: response.razorpay_order_id,
                  provider_payment_id: response.razorpay_payment_id,
                  provider_signature: response.razorpay_signature,
                  payment_method: paymentMethod,
                },
              }).unwrap();

              if (verifyRes.data) {
                const confirmedBookingId =
                  verifyRes.data.booking_id || reservation.id;
                navigate(
                  `/bookings/confirmation?bookingId=${confirmedBookingId}`
                );
              }
            } catch (err: unknown) {
              const errorObj = err as { data?: { message?: string } };
              setErrorMessage(
                errorObj.data?.message || t("payment:paymentFailed")
              );
            }
          },
        };

        const rzp = new window.Razorpay(options);
        rzp.on("payment.failed", (response: RazorpayFailureResponse) => {
          setErrorMessage(
            response.error.description || t("payment:paymentFailed")
          );
        });
        rzp.open();
        return;
      }

      // 3. Fallback / Mock provider simulation
      const dummyPaymentId = `pay_mock_${Date.now().toString().slice(-6)}`;
      const verifyRes = await verifyPayment({
        paymentId: payment.id,
        body: {
          provider_order_id: payment.provider_order_id || "",
          provider_payment_id: dummyPaymentId,
          provider_signature: "mock_signature_bypass",
          payment_method: paymentMethod,
        },
      }).unwrap();

      if (verifyRes.data) {
        const confirmedBookingId = verifyRes.data.booking_id || reservation.id;
        navigate(`/bookings/confirmation?bookingId=${confirmedBookingId}`);
      }
    } catch (err: unknown) {
      const errorObj = err as { data?: { message?: string } };
      setErrorMessage(errorObj.data?.message || t("payment:paymentFailed"));
    }
  };

  const handleCancelReservation = async () => {
    if (!reservation) return;
    try {
      await cancelReservation(reservation.id).unwrap();
      navigate(
        reservation.therapist_id
          ? `/therapists/${reservation.therapist_id}`
          : "/therapists"
      );
    } catch {
      navigate("/therapists");
    }
  };

  if (!reservationId) {
    return (
      <Container maxWidth="sm" className="py-16 text-center">
        <Typography variant="h6" className="text-neutral-700">
          No reservation found. Please select an available slot first.
        </Typography>
        <Button
          variant="contained"
          className="mt-4 bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
          onClick={() => navigate("/therapists")}
        >
          Browse Therapists
        </Button>
      </Container>
    );
  }

  if (isResLoading) {
    return (
      <Box className="flex justify-center items-center min-h-[60vh]">
        <CircularProgress className="text-teal-600" />
      </Box>
    );
  }

  if (resError || !reservation) {
    return (
      <Container maxWidth="sm" className="py-16 text-center">
        <Box className="p-6 bg-red-50 text-red-700 rounded-2xl border border-red-200">
          <Typography variant="h6" className="font-bold mb-2">
            Reservation Expired or Not Found
          </Typography>
          <Typography variant="body2" className="mb-4">
            {t("booking:reservation.expired")}
          </Typography>
          <Button
            variant="contained"
            className="bg-teal-600 hover:bg-teal-700 text-white rounded-xl"
            onClick={() => navigate("/therapists")}
          >
            Find Another Slot
          </Button>
        </Box>
      </Container>
    );
  }

  const startDate = new Date(reservation.start_at);
  const formattedDate = startDate.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = startDate.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Container maxWidth="md" className="py-10">
      <Box className="max-w-xl mx-auto space-y-6">
        <Typography
          variant="h4"
          className="font-bold text-neutral-900 text-center"
        >
          {t("payment:checkoutTitle")}
        </Typography>

        <ReservationTimer
          expiresAt={reservation.expires_at}
          onExpire={() => navigate("/therapists")}
        />

        {errorMessage && (
          <Box className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">
            <Typography variant="body2">{errorMessage}</Typography>
          </Box>
        )}

        <Card className="rounded-2xl border border-neutral-200 shadow-sm overflow-hidden">
          <CardContent className="p-6 space-y-6">
            <Typography variant="h6" className="font-bold text-neutral-900">
              {t("payment:orderSummary")}
            </Typography>

            <Box className="space-y-3 text-sm">
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("payment:therapist")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  {therapist?.display_name || "Consultant"}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("payment:sessionMode")}:
                </span>
                <span className="font-semibold text-neutral-900 capitalize">
                  {reservation.session_mode.replace("_", " ")}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("payment:dateTime")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  {formattedDate} at {formattedTime}
                </span>
              </Box>
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("payment:duration")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  {reservation.duration_minutes} mins
                </span>
              </Box>

              <Divider className="my-2" />

              {/* Package Credit Section */}
              {usablePackages.length > 0 && (
                <Box className="space-y-2 py-2">
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-neutral-800"
                  >
                    {t("payment:packageRedemption")}
                  </Typography>
                  {usablePackages.map((pkg) => {
                    const isSelected = selectedPackageId === pkg.id;
                    return (
                      <Box
                        key={pkg.id}
                        onClick={() => handleSelectPackage(pkg.id)}
                        className={`p-3 rounded-xl border cursor-pointer flex justify-between items-center transition-all ${
                          isSelected
                            ? "border-teal-600 bg-teal-50/50"
                            : "border-neutral-200 hover:border-neutral-300"
                        }`}
                      >
                        <Box>
                          <Typography
                            variant="body2"
                            className="font-semibold text-neutral-900"
                          >
                            {pkg.title}
                          </Typography>
                          <Typography
                            variant="caption"
                            className="text-neutral-500"
                          >
                            {t("payment:packageSessionBalance", {
                              count: pkg.remaining_sessions,
                            })}
                          </Typography>
                        </Box>
                        <Chip
                          label={isSelected ? "Applied" : "Use Session"}
                          color={isSelected ? "primary" : "default"}
                          size="small"
                          className="capitalize font-medium"
                        />
                      </Box>
                    );
                  })}
                  <Divider className="my-2" />
                </Box>
              )}

              {/* Coupon Section (Only if no package selected) */}
              {!selectedPackageId && (
                <Box className="space-y-2 py-1">
                  <Typography
                    variant="subtitle2"
                    className="font-bold text-neutral-800 flex items-center gap-1.5"
                  >
                    <FiTag className="text-teal-600" />
                    {t("offer:haveCoupon")}
                  </Typography>
                  {appliedCoupon ? (
                    <Box className="flex justify-between items-center p-2.5 bg-green-50 border border-green-200 rounded-xl">
                      <Box>
                        <Typography
                          variant="body2"
                          className="font-bold text-green-800"
                        >
                          {appliedCoupon}
                        </Typography>
                        <Typography
                          variant="caption"
                          className="text-green-600"
                        >
                          -₹{(discountMinor / 100).toFixed(0)} off
                        </Typography>
                      </Box>
                      <Button
                        size="small"
                        color="error"
                        onClick={handleRemoveCoupon}
                        className="text-xs capitalize font-medium"
                      >
                        {t("offer:remove")}
                      </Button>
                    </Box>
                  ) : (
                    <Box className="flex gap-2">
                      <TextField
                        size="small"
                        placeholder={t("offer:couponCodePlaceholder")}
                        value={couponInput}
                        onChange={(e) => setCouponInput(e.target.value)}
                        fullWidth
                      />
                      <Button
                        variant="outlined"
                        onClick={handleApplyCoupon}
                        disabled={isValidatingOffer || !couponInput.trim()}
                        className="border-teal-600 text-teal-700 hover:bg-teal-50 capitalize rounded-lg px-4"
                      >
                        {isValidatingOffer ? (
                          <CircularProgress size={16} />
                        ) : (
                          t("offer:apply")
                        )}
                      </Button>
                    </Box>
                  )}
                  <Divider className="my-2" />
                </Box>
              )}

              {/* Pricing breakdown lines */}
              <Box className="flex justify-between">
                <span className="text-neutral-500">
                  {t("payment:basePrice")}:
                </span>
                <span className="font-semibold text-neutral-900">
                  ₹{(basePriceMinor / 100).toFixed(0)}
                </span>
              </Box>

              {(discountMinor > 0 || selectedPackageId) && (
                <Box className="flex justify-between text-green-600">
                  <span>{t("payment:discount")}:</span>
                  <span className="font-semibold">
                    -₹
                    {selectedPackageId
                      ? (basePriceMinor / 100).toFixed(0)
                      : (discountMinor / 100).toFixed(0)}
                  </span>
                </Box>
              )}

              <Box className="flex justify-between items-center text-base pt-2">
                <span className="font-bold text-neutral-900">
                  {t("payment:totalPayable")}:
                </span>
                <span className="font-bold text-2xl text-teal-700">
                  ₹{(payableMinor / 100).toFixed(0)}
                </span>
              </Box>
            </Box>

            {/* Payment Method Selector (if payable > 0) */}
            {payableMinor > 0 ? (
              <Box className="space-y-3 pt-2">
                <Typography
                  variant="subtitle2"
                  className="font-bold text-neutral-800 flex items-center gap-1.5"
                >
                  <FiCreditCard className="text-teal-600" />
                  {t("payment:choosePaymentMethod")}
                </Typography>
                <RadioGroup
                  value={paymentMethod}
                  onChange={(e) =>
                    setPaymentMethod(
                      e.target.value as "upi" | "card" | "netbanking"
                    )
                  }
                  className="gap-2"
                >
                  <FormControlLabel
                    value="upi"
                    control={<Radio color="primary" />}
                    label={t("payment:upi")}
                    className="border border-neutral-200 rounded-xl px-3 py-1 m-0 hover:bg-neutral-50"
                  />
                  <FormControlLabel
                    value="card"
                    control={<Radio color="primary" />}
                    label={t("payment:card")}
                    className="border border-neutral-200 rounded-xl px-3 py-1 m-0 hover:bg-neutral-50"
                  />
                  <FormControlLabel
                    value="netbanking"
                    control={<Radio color="primary" />}
                    label={t("payment:netbanking")}
                    className="border border-neutral-200 rounded-xl px-3 py-1 m-0 hover:bg-neutral-50"
                  />
                </RadioGroup>
              </Box>
            ) : (
              <Box className="p-3 bg-teal-50 text-teal-800 rounded-xl border border-teal-200 text-sm">
                {t("payment:usePackageCredit", {
                  title:
                    usablePackages.find((p) => p.id === selectedPackageId)
                      ?.title || "Package",
                })}
              </Box>
            )}

            <TextField
              fullWidth
              multiline
              rows={2}
              label={t("booking:confirm.notesLabel")}
              placeholder={t("booking:confirm.notesPlaceholder")}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-2"
            />

            <Box className="flex items-center gap-2 text-xs text-neutral-500">
              <FiShield className="text-teal-600 flex-shrink-0" />
              <span>{t("booking:confirm.terms")}</span>
            </Box>

            <Box className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button
                variant="outlined"
                color="inherit"
                fullWidth
                disabled={isProcessing || isCancelling}
                onClick={handleCancelReservation}
                startIcon={<FiXCircle />}
                className="rounded-xl py-2.5 text-neutral-600 capitalize"
              >
                {t("booking:reservation.cancel")}
              </Button>

              <Button
                variant="contained"
                fullWidth
                disabled={isProcessing || isCancelling}
                onClick={handlePaymentSubmit}
                startIcon={
                  isProcessing ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    <FiCheckCircle />
                  )
                }
                className="rounded-xl py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold capitalize shadow-none"
              >
                {isProcessing
                  ? t("payment:processingPayment")
                  : payableMinor === 0
                    ? t("payment:redeemNow")
                    : t("payment:payNow", {
                        amount: (payableMinor / 100).toFixed(0),
                      })}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};
