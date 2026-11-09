import os
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import create_engine, DateTime, ForeignKey, Numeric, String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./local.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Trade(Base):
    __tablename__ = 'trades'
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), index=True)
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Side(str, Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class TradeIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=12, pattern=r'^[A-Za-z][A-Za-z0-9.]*$')
    side: Side
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)

class TradeOut(TradeIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

app = FastAPI(title='Trade Workflow API', version='0.1.0')

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)  # Learning stage only; replace with Alembic migrations.

def get_db():
    with SessionLocal() as session:
        yield session

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/trades/count')
def count_trades(db: Session = Depends(get_db)):
    count=db.query(Trade).count()
    return {"count": count}

@app.post('/trades', response_model=TradeOut, status_code=201)
def create_trade(payload: TradeIn, db: Session = Depends(get_db)):
    trade = Trade(**payload.model_dump(exclude={'side', 'symbol'}), side=payload.side.value, symbol=payload.symbol.upper())
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade

@app.get('/trades', response_model=list[TradeOut])
def list_trades(symbol: str | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    stmt = select(Trade).order_by(Trade.id.desc()).offset(offset).limit(limit)
    if symbol:
        stmt = select(Trade).where(Trade.symbol == symbol.upper()).order_by(Trade.id.desc()).offset(offset).limit(limit)
    return db.scalars(stmt).all()

@app.get('/trades/{trade_id}', response_model=TradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail='Trade not found')
    return trade

@app.delete('/trades/{trade_id}', status_code=204)
def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail='Trade not found')
    db.delete(trade)
    db.commit()

@app.get('/reports/notional-by-symbol')
def report(db: Session = Depends(get_db)):
    stmt = select(Trade.symbol, func.count(Trade.id), func.sum(Trade.quantity * Trade.price)).group_by(Trade.symbol).order_by(Trade.symbol)
    return [{'symbol': symbol, 'trade_count': count, 'total_notional': str(total)} for symbol, count, total in db.execute(stmt)]
