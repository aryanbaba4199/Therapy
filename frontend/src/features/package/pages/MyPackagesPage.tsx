import React from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Grid,
  LinearProgress,
  Typography,
} from "@mui/material";
import { FiPackage, FiCalendar, FiCheckCircle } from "react-icons/fi";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useListMyPackagesQuery } from "../api/package_api";

export const MyPackagesPage: React.FC = () => {
  const { t } = useTranslation(["payment", "common"]);
  const navigate = useNavigate();
  const { data: myPackagesData, isLoading } = useListMyPackagesQuery();
  const userPackages = myPackagesData?.data || [];

  return (
    <Container maxWidth="lg" className="py-12">
      <Box className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <Box>
          <Typography
            variant="h4"
            className="font-extrabold text-neutral-900 tracking-tight"
          >
            {t("payment:myPackages")}
          </Typography>
          <Typography variant="subtitle1" className="text-neutral-500">
            {t("payment:myPackagesSubtitle")}
          </Typography>
        </Box>
        <Button
          variant="contained"
          onClick={() => navigate("/packages")}
          className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2.5 px-5 rounded-xl shadow-none capitalize"
        >
          {t("payment:buyPackage")}
        </Button>
      </Box>

      {isLoading ? (
        <Box className="flex justify-center items-center py-20">
          <CircularProgress className="text-teal-600" />
        </Box>
      ) : userPackages.length === 0 ? (
        <Card className="text-center py-16 px-4 rounded-3xl border border-neutral-200 shadow-none bg-neutral-50/50">
          <Box className="w-16 h-16 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center mx-auto mb-4">
            <FiPackage size={32} />
          </Box>
          <Typography variant="h6" className="font-bold text-neutral-800 mb-1">
            {t("payment:noUsablePackages")}
          </Typography>
          <Typography
            variant="body2"
            className="text-neutral-500 max-w-sm mx-auto mb-6"
          >
            Get session bundles to enjoy discounted rates and hassle-free
            1-click booking checkouts.
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate("/packages")}
            className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2.5 px-6 rounded-xl shadow-none capitalize"
          >
            {t("payment:buyPackage")}
          </Button>
        </Card>
      ) : (
        <Grid container spacing={4}>
          {userPackages.map((pkg) => {
            const usedSessions = pkg.total_sessions - pkg.remaining_sessions;
            const progressPercent = (usedSessions / pkg.total_sessions) * 100;
            const expiryDate = new Date(pkg.expires_at).toLocaleDateString(
              undefined,
              {
                year: "numeric",
                month: "short",
                day: "numeric",
              }
            );

            return (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={pkg.id}>
                <Card className="rounded-3xl border border-neutral-200 overflow-hidden shadow-sm hover:shadow-md transition-all">
                  <CardContent className="p-6 space-y-5">
                    <Box className="flex justify-between items-start">
                      <Typography
                        variant="h6"
                        className="font-bold text-neutral-900"
                      >
                        {pkg.title}
                      </Typography>
                      <Chip
                        label={pkg.status}
                        size="small"
                        color={pkg.status === "active" ? "success" : "default"}
                        className="capitalize font-semibold text-xs"
                      />
                    </Box>

                    <Box className="space-y-2">
                      <Box className="flex justify-between text-sm">
                        <span className="text-neutral-500">
                          Sessions Balance
                        </span>
                        <span className="font-bold text-neutral-900">
                          {pkg.remaining_sessions} of {pkg.total_sessions} left
                        </span>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={progressPercent}
                        className="h-2 rounded-full bg-neutral-100"
                        sx={{
                          "& .MuiLinearProgress-bar": {
                            backgroundColor: "#0d9488",
                          },
                        }}
                      />
                    </Box>

                    <Box className="space-y-2 text-xs text-neutral-500 pt-2 border-t border-neutral-100">
                      <Box className="flex items-center gap-2">
                        <FiCalendar className="text-teal-600" />
                        <span>Valid until {expiryDate}</span>
                      </Box>
                      <Box className="flex items-center gap-2">
                        <FiCheckCircle className="text-teal-600" />
                        <span>Instant 1-click booking deduction</span>
                      </Box>
                    </Box>

                    {pkg.status === "active" && pkg.remaining_sessions > 0 && (
                      <Button
                        variant="outlined"
                        fullWidth
                        onClick={() => navigate("/therapists")}
                        className="rounded-xl py-2 border-teal-600 text-teal-700 hover:bg-teal-50 capitalize font-semibold"
                      >
                        Book a Session
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Container>
  );
};
