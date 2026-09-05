import React, { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  Radio,
  RadioGroup,
  FormControlLabel,
  Typography,
} from "@mui/material";
import { FiCheck, FiPackage, FiShield } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useListPackagesQuery, type PackageProduct } from "../api/package_api";
import {
  useInitiatePaymentMutation,
  useVerifyPaymentMutation,
} from "@/features/payment/api/payment_api";

export const PackageListPage: React.FC = () => {
  const { t } = useTranslation(["payment", "common"]);
  const navigate = useNavigate();
  const { data: packagesData, isLoading } = useListPackagesQuery();
  const packages = packagesData?.data || [];

  const [selectedPackage, setSelectedPackage] = useState<PackageProduct | null>(
    null
  );
  const [paymentMethod, setPaymentMethod] = useState<
    "upi" | "card" | "netbanking"
  >("upi");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [initiatePayment, { isLoading: isInitiating }] =
    useInitiatePaymentMutation();
  const [verifyPayment, { isLoading: isVerifying }] =
    useVerifyPaymentMutation();

  const isPurchasing = isInitiating || isVerifying;

  const handlePurchase = async () => {
    if (!selectedPackage) return;
    try {
      setErrorMessage(null);
      const initRes = await initiatePayment({
        target_type: "package",
        target_id: selectedPackage.id,
        payment_method: paymentMethod,
        idempotency_key: `pkg-pay-${selectedPackage.id}-${Date.now()}`,
      }).unwrap();

      const payment = initRes.data;
      if (!payment) throw new Error("Failed to initiate payment");

      const dummyPaymentId = `pay_mock_${Date.now().toString().slice(-6)}`;
      await verifyPayment({
        paymentId: payment.id,
        body: {
          provider_order_id: payment.provider_order_id,
          provider_payment_id: dummyPaymentId,
          provider_signature: "mock_signature_bypass",
        },
      }).unwrap();

      setSelectedPackage(null);
      navigate("/packages/my");
    } catch (err: unknown) {
      const errorObj = err as { data?: { message?: string } };
      setErrorMessage(errorObj.data?.message || t("payment:paymentFailed"));
    }
  };

  return (
    <Container maxWidth="lg" className="py-12">
      <Box className="text-center max-w-2xl mx-auto mb-12 space-y-3">
        <Typography
          variant="h3"
          className="font-extrabold text-neutral-900 tracking-tight"
        >
          {t("payment:packages")}
        </Typography>
        <Typography variant="subtitle1" className="text-neutral-600">
          {t("payment:packagesSubtitle")}
        </Typography>
      </Box>

      {isLoading ? (
        <Box className="flex justify-center items-center py-20">
          <CircularProgress className="text-teal-600" />
        </Box>
      ) : (
        <Grid container spacing={4} sx={{ justifyContent: "center" }}>
          {packages.map((pkg) => {
            const priceRupees = (pkg.price_minor / 100).toFixed(0);
            const perSessionRupees = (
              pkg.price_minor /
              100 /
              pkg.session_count
            ).toFixed(0);

            return (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={pkg.id}>
                <Card className="h-full flex flex-col justify-between rounded-3xl border border-neutral-200 hover:border-teal-400 hover:shadow-lg transition-all duration-300 overflow-hidden">
                  <CardContent className="p-8 space-y-6 flex-1">
                    <Box className="flex justify-between items-start">
                      <Box className="w-12 h-12 rounded-2xl bg-teal-50 flex items-center justify-center text-teal-600">
                        <FiPackage size={24} />
                      </Box>
                      <Chip
                        label={t("payment:validity", {
                          days: pkg.validity_days,
                        })}
                        size="small"
                        className="bg-neutral-100 text-neutral-700 font-medium"
                      />
                    </Box>

                    <Box>
                      <Typography
                        variant="h5"
                        className="font-bold text-neutral-900 mb-1"
                      >
                        {pkg.title}
                      </Typography>
                      <Typography
                        variant="body2"
                        className="text-neutral-500 line-clamp-2"
                      >
                        {pkg.description}
                      </Typography>
                    </Box>

                    <Box className="space-y-1">
                      <Box className="flex items-baseline gap-1">
                        <span className="text-4xl font-black text-neutral-900">
                          ₹{priceRupees}
                        </span>
                        <span className="text-sm text-neutral-500 font-medium">
                          total
                        </span>
                      </Box>
                      <Typography
                        variant="caption"
                        className="text-teal-700 font-semibold block"
                      >
                        {t("payment:pricePerSession", {
                          amount: perSessionRupees,
                        })}
                      </Typography>
                    </Box>

                    <Divider />

                    <Box className="space-y-3">
                      <Box className="flex items-center gap-2.5 text-sm text-neutral-700">
                        <FiCheck className="text-teal-600 flex-shrink-0" />
                        <span>
                          {t("payment:sessionsCount", {
                            count: pkg.session_count,
                          })}
                        </span>
                      </Box>
                      <Box className="flex items-center gap-2.5 text-sm text-neutral-700">
                        <FiCheck className="text-teal-600 flex-shrink-0" />
                        <span>Usable with any verified therapist</span>
                      </Box>
                      <Box className="flex items-center gap-2.5 text-sm text-neutral-700">
                        <FiCheck className="text-teal-600 flex-shrink-0" />
                        <span>Flexible online / offline booking</span>
                      </Box>
                    </Box>
                  </CardContent>

                  <Box className="p-8 pt-0">
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => setSelectedPackage(pkg)}
                      className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 rounded-2xl shadow-none capitalize"
                    >
                      {t("payment:buyPackage")}
                    </Button>
                  </Box>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Package Purchase Modal */}
      <Dialog
        open={Boolean(selectedPackage)}
        onClose={() => !isPurchasing && setSelectedPackage(null)}
        maxWidth="xs"
        fullWidth
        slotProps={{ paper: { className: "rounded-3xl p-2" } }}
      >
        <DialogTitle className="font-bold text-neutral-900 pb-2">
          {t("payment:buyPackage")}
        </DialogTitle>
        <DialogContent className="space-y-4 pt-2">
          {errorMessage && (
            <Box className="p-3 bg-red-50 text-red-700 rounded-xl border border-red-200 text-sm">
              {errorMessage}
            </Box>
          )}

          {selectedPackage && (
            <Box className="space-y-4">
              <Box className="p-4 bg-teal-50/60 rounded-2xl border border-teal-100 space-y-1">
                <Typography
                  variant="subtitle1"
                  className="font-bold text-teal-950"
                >
                  {selectedPackage.title}
                </Typography>
                <Typography
                  variant="h5"
                  className="font-extrabold text-teal-700"
                >
                  ₹{(selectedPackage.price_minor / 100).toFixed(0)}
                </Typography>
              </Box>

              <Box className="space-y-2">
                <Typography
                  variant="body2"
                  className="font-semibold text-neutral-800"
                >
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

              <Box className="flex items-center gap-2 text-xs text-neutral-500">
                <FiShield className="text-teal-600 flex-shrink-0" />
                <span>Secure 256-bit encrypted transaction</span>
              </Box>

              <Box className="flex gap-2 pt-2">
                <Button
                  variant="outlined"
                  fullWidth
                  disabled={isPurchasing}
                  onClick={() => setSelectedPackage(null)}
                  className="rounded-xl py-2.5 text-neutral-600 capitalize"
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  fullWidth
                  disabled={isPurchasing}
                  onClick={handlePurchase}
                  className="rounded-xl py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold capitalize shadow-none"
                >
                  {isPurchasing ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    t("payment:payNow", {
                      amount: (selectedPackage.price_minor / 100).toFixed(0),
                    })
                  )}
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
};
