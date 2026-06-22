import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.SalesReportingUseCase")


class SalesReportingUseCase:
    """
    Application Layer: Generates financial reports and analysis for sales.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session, context.business_id)

    def get_daily_report(self, date: str) -> ServiceResponse:
        try:
            total = self.repo.get_daily_totals(date)
            breakdown = self.repo.get_daily_breakdown(date)

            split_data = {row["payment_method"]: float(row["sum"]) for row in breakdown}

            return ServiceResponse.success_res(
                data={"total": total, "breakdown": split_data},
                message=f"Financial report for {date} generated successfully.",
            )
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return ServiceResponse.error_res(
                f"Report failure: {str(e)}", "REPORT_ERROR"
            )
